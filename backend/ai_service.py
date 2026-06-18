import json
import logging

from config import Config
from deepseek_client import deepseek
from gigachat_client import gigachat
from database import get_db
from dialog_hints import apply_message_hints
from web_search_service import fetch_web_context
from llm_common import (
    build_dialog_messages,
    build_tour_prompt,
    default_collected,
    extract_json,
    fallback_tour,
    finalize_tour,
    parse_dialog_response,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROVIDERS = {
    "deepseek": deepseek,
    "gigachat": gigachat,
}

DISPLAY_NAMES = {
    "deepseek": "DeepSeek",
    "gigachat": "GigaChat (Сбер)",
}


class AIService:
    def _resolve_provider(self, provider: str | None) -> str:
        p = (provider or Config.LLM_PROVIDER or "auto").lower().strip()
        if p in PROVIDERS:
            return p
        return "auto"

    def _client_order(self, provider: str) -> list:
        if provider == "auto":
            primary = getattr(Config, "LLM_PRIMARY", "deepseek") or "deepseek"
            primary = primary.lower()
            secondary = "gigachat" if primary == "deepseek" else "deepseek"
            order = [primary, secondary]
        else:
            order = [provider]
            if getattr(Config, "LLM_FALLBACK", True):
                other = "gigachat" if provider == "deepseek" else "deepseek"
                if other not in order:
                    order.append(other)
        clients = [PROVIDERS[name] for name in order if name in PROVIDERS]
        if not clients and "deepseek" in PROVIDERS:
            clients = [PROVIDERS["deepseek"]]
        return clients

    async def process_message(
        self, user_message: str, dialog_state: dict, provider: str | None = None
    ):
        collected = dialog_state.get("collected") or default_collected()
        # Серверные эвристики: вытаскиваем даты/длительность из текста до LLM
        collected = apply_message_hints(user_message, collected)
        dialog_state["collected"] = collected
        source = "demo" if dialog_state.get("demo_mode") else None
        catalog_rows = get_db().get_all_hotels_sample(limit=50, source_site=source)
        web_context, web_query = await fetch_web_context(user_message, collected)
        if web_query:
            logger.info("Web search: %s", web_query)
        messages = build_dialog_messages(
            user_message, collected, catalog_rows, web_context=web_context
        )
        resolved = self._resolve_provider(provider)
        errors = []
        clients = self._client_order(resolved)
        tried: list[str] = []

        if not clients:
            logger.error("No LLM clients available")
            return (
                "Извините, сервис подбора временно недоступен. Пожалуйста, свяжитесь с нами по телефону +7(4162) 317-771.",
                dialog_state,
                False,
                {"llm_provider": None, "llm_fallback": False, "llm_tried": []},
            )

        for idx, client in enumerate(clients):
            tried.append(client.name)
            logger.info(f"LLM dialog via {client.name}")
            try:
                response = await client.chat(messages)
            except Exception as e:
                logger.error(f"{client.name} chat() exception: {e}")
                errors.append(
                    f"{DISPLAY_NAMES.get(client.name, client.name)}: ошибка вызова"
                )
                continue

            if response:
                try:
                    text, state, ready = parse_dialog_response(
                        response, dialog_state, collected, catalog_rows
                    )
                    # Повторно применяем эвристики после ответа LLM
                    state["collected"] = apply_message_hints(
                        user_message, state.get("collected") or {}
                    )
                    state["llm_provider"] = client.name
                    ready = bool(ready)
                    # Если всё собрано, но модель продолжает уточнять — закрываем цикл.
                    c = state.get("collected") or {}
                    if (
                        c.get("destination")
                        and c.get("date_from")
                        and c.get("date_to")
                        and c.get("budget") is not None
                    ):
                        ready = True
                        text = (
                            "Отлично, все параметры собраны. Подбираю перелёт, "
                            "проживание и готовые туры из каталога..."
                        )
                    meta = {
                        "llm_provider": client.name,
                        "llm_provider_label": DISPLAY_NAMES.get(
                            client.name, client.name
                        ),
                        "llm_fallback": idx > 0,
                        "llm_tried": list(tried),
                        "web_search_used": bool(web_context),
                        "web_search_query": web_query,
                    }
                    return text, state, ready, meta
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"{client.name} JSON parse: {e}")
                    errors.append(
                        f"{DISPLAY_NAMES.get(client.name, client.name)}: неверный формат"
                    )
                except Exception as e:
                    logger.error(f"{client.name} unexpected: {e}")
                    errors.append(
                        f"{DISPLAY_NAMES.get(client.name, client.name)}: внутренняя ошибка"
                    )
            else:
                err = getattr(client, "last_error", "") or "нет ответа"
                errors.append(f"{DISPLAY_NAMES.get(client.name, client.name)}: {err}")

        detail = "; ".join(errors) if errors else "неизвестная ошибка"
        return (
            f"Сервис ИИ временно недоступен. Пожалуйста, позвоните нам: +7(4162) 317-771. ({detail})",
            dialog_state,
            False,
            {
                "llm_provider": None,
                "llm_fallback": len(tried) > 1,
                "llm_tried": tried,
            },
        )

    async def generate_tour(
        self, collected_params: dict, hotels_data: list, provider: str | None = None
    ):
        prompt = build_tour_prompt(collected_params, hotels_data)
        messages = [{"role": "user", "content": prompt}]
        resolved = self._resolve_provider(provider)
        clients = self._client_order(resolved)

        if not clients:
            return fallback_tour(hotels_data, collected_params.get("destination"))

        for client in clients:
            logger.info(f"LLM tour via {client.name}")
            try:
                response = await client.chat(messages)
            except Exception:
                continue
            if response:
                try:
                    tour = extract_json(response)
                    tour = finalize_tour(
                        tour, hotels_data, collected_params.get("destination")
                    )
                    tour["_llm_provider"] = client.name
                    return tour
                except (json.JSONDecodeError, TypeError):
                    continue
        return fallback_tour(hotels_data, collected_params.get("destination"))

    def list_providers(self) -> list[dict]:
        return [
            {"id": "deepseek", "name": DISPLAY_NAMES["deepseek"]},
            {"id": "gigachat", "name": DISPLAY_NAMES["gigachat"]},
            {"id": "auto", "name": "Авто (с запасным)"},
        ]


ai = AIService()
