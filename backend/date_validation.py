"""Проверка дат поездки (не полагаемся только на ответ LLM)."""
from datetime import date, datetime, timedelta
from typing import Any


def today() -> date:
    return date.today()


def today_iso() -> str:
    return today().isoformat()


def parse_travel_date(value: Any) -> date | None:
    """Парсит YYYY-MM-DD или DD.MM.YYYY."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    s = str(value).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s[:10] if fmt == "%Y-%m-%d" else s, fmt).date()
        except ValueError:
            continue
    return None


def format_date_ru(d: date) -> str:
    months = (
        "января",
        "февраля",
        "марта",
        "апреля",
        "мая",
        "июня",
        "июля",
        "августа",
        "сентября",
        "октября",
        "ноября",
        "декабря",
    )
    return f"{d.day} {months[d.month - 1]} {d.year}"


def validate_collected_dates(collected: dict) -> tuple[bool, str | None, dict]:
    """
    Проверяет date_from / date_to в collected.
    Возвращает (ok, сообщение_пользователю, обновлённый collected).
    """
    collected = dict(collected or {})
    d_from = parse_travel_date(collected.get("date_from"))
    d_to = parse_travel_date(collected.get("date_to"))

    if not d_from and collected.get("date_from"):
        return (
            False,
            "Не удалось разобрать дату начала поездки. Укажите, пожалуйста, в формате "
            "«10 июля 2026» или «2026-07-10».",
            collected,
        )
    if not d_to and collected.get("date_to"):
        return (
            False,
            "Не удалось разобрать дату окончания. Укажите дату возвращения, например «20 августа 2026».",
            collected,
        )

    if d_from is None or d_to is None:
        return True, None, collected

    # Нормализуем в ISO для БД и промптов
    collected["date_from"] = d_from.isoformat()
    collected["date_to"] = d_to.isoformat()

    t = today()

    if d_from < t:
        collected["date_from"] = None
        collected["date_to"] = None
        return (
            False,
            f"Дата начала ({format_date_ru(d_from)}) уже прошла. "
            f"Сегодня {format_date_ru(t)}. Укажите даты в будущем.",
            collected,
        )

    if d_to < t:
        collected["date_from"] = None
        collected["date_to"] = None
        return (
            False,
            f"Дата окончания ({format_date_ru(d_to)}) уже прошла. "
            f"Сегодня {format_date_ru(t)}. Укажите актуальные даты поездки.",
            collected,
        )

    if d_to < d_from:
        collected["date_from"] = None
        collected["date_to"] = None
        return (
            False,
            "Дата окончания не может быть раньше даты начала. "
            f"Вы указали: с {format_date_ru(d_from)} по {format_date_ru(d_to)}. "
            "Исправьте, пожалуйста.",
            collected,
        )

    if (d_to - d_from).days > 365:
        return (
            False,
            "Слишком длинный период (больше года). Уточните даты поездки.",
            collected,
        )

    if d_from == d_to:
        return (
            False,
            "Даты начала и окончания совпадают. Укажите период хотя бы на 1–2 дня.",
            collected,
        )

    return True, None, collected


def all_required_fields_present(collected: dict) -> bool:
    return bool(
        collected.get("destination")
        and collected.get("date_from")
        and collected.get("date_to")
        and collected.get("budget") is not None
    )
