"""Правила пост-обработки пользовательского ввода для стабильного диалога."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from date_validation import parse_travel_date, today

MONTHS_RU = {
    "январ": 1,
    "феврал": 2,
    "март": 3,
    "апрел": 4,
    "ма": 5,  # май / мая
    "июн": 6,
    "июл": 7,
    "август": 8,
    "сентябр": 9,
    "октябр": 10,
    "ноябр": 11,
    "декабр": 12,
}


def _parse_year(y: str | None, base_year: int) -> int:
    if not y:
        return base_year
    y = y.strip()
    if len(y) == 2 and y.isdigit():
        return 2000 + int(y)
    if y.isdigit() and len(y) == 4:
        return int(y)
    return base_year


def _month_from_word(w: str) -> int | None:
    lw = w.lower()
    for k, v in MONTHS_RU.items():
        if k in lw:
            return v
    return None


def _normalize_future(d: date) -> date:
    """Если дата без года уже прошла — сдвигаем на следующий год."""
    t = today()
    if d < t:
        try:
            return d.replace(year=d.year + 1)
        except ValueError:
            return d + timedelta(days=365)
    return d


def _extract_range(text: str, ref_year: int) -> tuple[date | None, date | None]:
    """
    Понимает:
    - "10 июня по 15 июня 2026"
    - "10 июня по 15"
    - "с 10 июня по 15 июня"
    """
    t = text.lower()
    m = re.search(
        r"(?:с\s*)?(\d{1,2})\s+([а-яё]+)(?:\s+(\d{2,4}))?\s*(?:по|-|до)\s*(\d{1,2})(?:\s+([а-яё]+))?(?:\s+(\d{2,4}))?",
        t,
        re.IGNORECASE,
    )
    if not m:
        return None, None

    d1, mon1, y1, d2, mon2, y2 = m.groups()
    m1 = _month_from_word(mon1)
    if not m1:
        return None, None
    m2 = _month_from_word(mon2) if mon2 else m1
    if not m2:
        return None, None

    year1 = _parse_year(y1, ref_year)
    year2 = _parse_year(y2, year1)
    try:
        dt1 = date(year1, m1, int(d1))
        dt2 = date(year2, m2, int(d2))
        return _normalize_future(dt1), _normalize_future(dt2)
    except ValueError:
        return None, None


def _extract_single_date(text: str, ref_year: int) -> date | None:
    """
    Понимает:
    - "15 июня 26"
    - "10 июня"
    """
    m = re.search(r"(\d{1,2})\s+([а-яё]+)(?:\s+(\d{2,4}))?", text.lower())
    if not m:
        return None
    d, mon, y = m.groups()
    mm = _month_from_word(mon)
    if not mm:
        return None
    yy = _parse_year(y, ref_year)
    try:
        return _normalize_future(date(yy, mm, int(d)))
    except ValueError:
        return None


def _extract_duration_days(text: str) -> int | None:
    m = re.search(r"\b(\d{1,2})\s*(дн(?:я|ей)?|сут(?:ок)?)\b", text.lower())
    if not m:
        return None
    n = int(m.group(1))
    if 1 <= n <= 60:
        return n
    return None


def apply_message_hints(user_message: str, collected: dict) -> dict:
    """
    Добавляет в collected данные, которые модель часто пропускает:
    - диапазон дат
    - одну дату (старт/финиш)
    - длительность в днях
    """
    c = dict(collected or {})
    um = (user_message or "").lower()
    ref_year = datetime.now().year

    # Если пользователь просит "другие варианты" — снимаем жёсткий фильтр по Москве.
    if "предлож" in um and (
        "друг" in um or "вариант" in um or um.strip() in {"предложи", "предложите"}
    ):
        c.pop("city_preference", None)

    # Если пользователь явно меняет направление на не-Москву, снимаем фильтр Москвы.
    if "моск" not in um and any(
        token in um
        for token in (
            "хабар",
            "китай",
            "таил",
            "турц",
            "вьет",
            "росси",
            "сочи",
            "питер",
            "санкт",
        )
    ):
        c.pop("city_preference", None)

    # Городовые предпочтения (для последующей фильтрации карточек)
    if "моск" in um:
        c["city_preference"] = "москва"
        if not c.get("destination"):
            c["destination"] = "Россия"

    # Нормализация распространённой опечатки
    if "хобаров" in um:
        if not c.get("destination"):
            c["destination"] = "Россия"

    # Сначала диапазон "с ... по ..."
    d_from, d_to = _extract_range(user_message, ref_year)
    if d_from and d_to:
        c["date_from"] = d_from.isoformat()
        c["date_to"] = d_to.isoformat()
        return c

    # Одиночная дата
    one = _extract_single_date(user_message, ref_year)
    if one:
        existing_from = parse_travel_date(c.get("date_from"))
        existing_to = parse_travel_date(c.get("date_to"))
        if existing_from and not existing_to and one >= existing_from:
            c["date_to"] = one.isoformat()
        elif existing_to and not existing_from and one <= existing_to:
            c["date_from"] = one.isoformat()
        elif not existing_from:
            c["date_from"] = one.isoformat()
        elif not existing_to:
            c["date_to"] = one.isoformat()

    # Длительность
    days = _extract_duration_days(user_message)
    if days:
        existing_from = parse_travel_date(c.get("date_from"))
        existing_to = parse_travel_date(c.get("date_to"))
        if existing_from and not existing_to:
            c["date_to"] = (existing_from + timedelta(days=days)).isoformat()
        elif existing_to and not existing_from:
            c["date_from"] = (existing_to - timedelta(days=days)).isoformat()

    return c
