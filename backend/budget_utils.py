"""Нормализация бюджета: в БД цены в рублях."""
from config import Config


def default_collected_fields() -> dict:
    return {
        "name": None,
        "destination": None,
        "date_from": None,
        "date_to": None,
        "budget": None,
        "budget_currency": "RUB",
        "preferences": None,
    }


def normalize_budget_rub(collected: dict) -> float | None:
    """
    Возвращает бюджет в рублях для фильтрации БД.
    budget — число; budget_currency — RUB (по умолчанию) или USD.
    """
    budget = collected.get("budget")
    if budget is None:
        return None
    try:
        amount = float(budget)
    except (TypeError, ValueError):
        return None

    currency = (collected.get("budget_currency") or "RUB").upper().strip()
    if currency in ("USD", "$"):
        return amount * Config.USD_TO_RUB
    return amount


def format_budget_display(collected: dict) -> str:
    budget = collected.get("budget")
    if budget is None:
        return "не указан"
    currency = (collected.get("budget_currency") or "RUB").upper()
    sym = "₽" if currency == "RUB" else "$"
    return f"{budget:,.0f}".replace(",", " ") + f" {sym}"
