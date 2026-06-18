import json
import re
from typing import Any

from budget_utils import default_collected_fields, normalize_budget_rub
from config import Config
from tour_links import apply_booking_links, resolve_agency_url, resolve_booking_url
from catalog_context import build_catalog_snippet, normalize_collected_destination
from date_validation import (
    all_required_fields_present,
    today_iso,
    validate_collected_dates,
)
from dialog_training import few_shot_examples


def extract_json(text: str) -> dict:
    if not text:
        raise json.JSONDecodeError("empty", text or "", 0)
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        text = fence.group(1)
    return json.loads(text)


def build_dialog_system_prompt(
    catalog_snippet: str = "", web_context: str = ""
) -> str:
    today = today_iso()
    catalog_block = catalog_snippet or "КАТАЛОГ: не загружен."
    web_block = ""
    if web_context:
        web_block = f"""
СПРАВКА ИЗ ИНТЕРНЕТА (используй для ответа на вопрос пользователя):
{web_context}
"""
    examples = few_shot_examples()
    return f"""
Ты — AI-ассистент туристической фирмы «Бон Вояж» / «Планета 360». Помогаешь подобрать тур из РЕАЛЬНОГО каталога.

СЕГОДНЯ: {today} (используй для проверки дат).

{catalog_block}
{web_block}
{examples}

ПРАВИЛА:
1. Общайся на русском, вежливо.
2. Извлекай: имя, направление (страна), date_from, date_to, budget (число), budget_currency, preferences.
3. destination — только страна/направление ИЗ КАТАЛОГА выше (или ближайшее совпадение: Хэйхэ → Китай).
4. Даты только YYYY-MM-DD в collected.
5. date_from и date_to НЕ РАНЬШЕ {today}; date_to ПОЗЖЕ date_from минимум на 1 день.
6. Прошлые или перепутанные даты → status "need_more", объясни ошибку.
7. Цены в каталоге в РУБЛЯХ. budget_currency: RUB по умолчанию, USD если пользователь указал $.
8. Один уточняющий вопрос за раз, если не хватает полей.
9. status "ready" только при валидных датах, бюджете и направлении из каталога.
10. Не выдумывай туры и цены — только каталог. Не давай советов про код/API.
11. Обязательно понимай русский формат дат: "10 июня", "15 июня 26", "с 10 июня по 15", "7 дней".
12. Хэйхэ, Шанхай, Бэйдайхэ — это направление «Китай». Благовещенск — вылет в Китай.
13. После ready система соберёт перелёт и проживание отдельно и покажет готовые туры из каталога.
14. Если есть блок «СПРАВКА ИЗ ИНТЕРНЕТА» — используй его для визы, погоды, документов, достопримечательностей; цены туров всё равно только из каталога.
15. Если справки из интернета нет — не выдумывай факты, предложи уточнить у менеджера +7(4162) 317-771.

Ответ — ТОЛЬКО JSON:
{{
  "status": "need_more" | "ready",
  "response": "текст пользователю",
  "collected": {{
    "name": null | "строка",
    "destination": null | "страна на русском",
    "date_from": null | "YYYY-MM-DD",
    "date_to": null | "YYYY-MM-DD",
    "budget": null | число,
    "budget_currency": "RUB" | "USD",
    "preferences": null | "строка"
  }}
}}
"""


def default_collected() -> dict[str, Any]:
    return default_collected_fields()


def build_dialog_messages(
    user_message: str,
    collected: dict,
    catalog_rows: list | None = None,
    web_context: str = "",
) -> list[dict]:
    snippet = build_catalog_snippet(catalog_rows or [])
    user_prompt = f"""
Уже собрано: {json.dumps(collected, ensure_ascii=False)}
Новое сообщение: "{user_message}"
Обнови collected и ответь.
"""
    return [
        {"role": "system", "content": build_dialog_system_prompt(snippet, web_context)},
        {"role": "user", "content": user_prompt},
    ]


def build_tour_prompt(collected_params: dict, hotels_data: list) -> str:
    budget_rub = normalize_budget_rub(collected_params)
    return f"""
Сформируй турпакет. Ответ — только JSON.

ПАРАМЕТРЫ:
{json.dumps(collected_params, ensure_ascii=False)}

Бюджет пользователя (в рублях): {budget_rub}
Период: {collected_params.get('date_from')} — {collected_params.get('date_to')}

ОТЕЛИ/ТУРЫ (выбирай ТОЛЬКО из списка, цены в РУБЛЯХ):
{json.dumps(hotels_data, ensure_ascii=False, default=str)}

Правила:
- selected_hotel — один тур из списка (лучшее соотношение цена/направление/бюджет).
- Не превышай бюджет {budget_rub} ₽ по total_price без предупреждения в recommendation_text.
- Перелёт оцени в рублях (~30% бюджета, если нет данных).
- В recommendation_text упомяни даты поездки и почему этот тур подходит.
- Все цены в JSON — в РУБЛЯХ.

JSON:
{{
  "selected_hotel": {{ "name": "", "price": 0, "description": "" }},
  "flight": {{ "estimated_price": 0, "info": "" }},
  "total_price": 0,
  "recommendation_text": "",
  "booking_links": {{
    "self": "URL страницы тура",
    "agency": "{Config.AGENCY_CONTACT_URL}"
  }}
}}
"""


def parse_dialog_response(
    response: str,
    dialog_state: dict,
    collected: dict,
    catalog_rows: list | None = None,
):
    parsed = extract_json(response)
    status = parsed.get("status", "need_more")
    response_text = parsed.get("response", "")
    new_collected = parsed.get("collected", collected)
    # Сохраняем служебные/уже собранные поля, которые LLM может "потерять"
    # (например city_preference при сообщении только с бюджетом).
    for keep_key in ("city_preference", "budget_currency", "name", "preferences"):
        if keep_key in collected and not new_collected.get(keep_key):
            new_collected[keep_key] = collected.get(keep_key)
    if not new_collected.get("budget_currency"):
        new_collected["budget_currency"] = "RUB"

    if catalog_rows:
        new_collected = normalize_collected_destination(new_collected, catalog_rows)

    # Серверная проверка дат (надёжнее, чем только ответ модели)
    dates_ok, date_msg, new_collected = validate_collected_dates(new_collected)
    if not dates_ok and date_msg:
        response_text = date_msg
        status = "need_more"

    dialog_state["collected"] = new_collected

    fields_ok = all_required_fields_present(new_collected)
    is_ready = status == "ready" and fields_ok and dates_ok

    if status == "ready" and fields_ok and dates_ok:
        is_ready = True
    elif fields_ok and dates_ok and status != "ready":
        # Модель забыла ready, но данные полные и валидны
        is_ready = True
    else:
        is_ready = False

    return response_text, dialog_state, is_ready


def finalize_tour(tour: dict, hotels_data: list, destination: str | None = None) -> dict:
    tour = apply_booking_links(tour, hotels_data, destination)
    tour["currency"] = "RUB"
    return tour


def fallback_tour(hotels_data: list, destination: str | None = None) -> dict:
    hotel = hotels_data[0] if hotels_data else {}
    price_rub = float(hotel.get("total_stay_price") or 0)
    dest = destination or hotel.get("destination", "")

    return finalize_tour(
        {
            "selected_hotel": {
                "name": hotel.get("name", "Тур"),
                "price": price_rub,
                "description": dest,
            },
            "flight": {"estimated_price": 0, "info": "Уточняйте у менеджера"},
            "total_price": price_rub,
            "recommendation_text": "Подобран вариант из каталога турфирмы.",
            "booking_links": {},
        },
        hotels_data,
        destination=dest,
    )
