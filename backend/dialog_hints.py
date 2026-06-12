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


def _extract_budget(text: str) -> tuple[float | None, str | None]:
    """Бюджет: 80 000 руб, 50к, $2000, до 120000 (не путаем с днями поездки)."""
    t = (text or "").lower().replace("\u00a0", " ")

    m = re.search(r"\$\s*(\d[\d\s]*)", t)
    if m:
        return float(m.group(1).replace(" ", "")), "USD"

    for pat in (
        r"(?:бюджет|до|около|примерно)\s*(\d[\d\s]{3,})(?:\s*(?:руб|₽|rub))?",
        r"(\d[\d\s]{4,})\s*(?:руб|₽|р\.?\b)",
        r"(?:^|[,;])\s*(\d{5,})\s*(?:$|[,;])",
    ):
        m = re.search(pat, t)
        if m:
            amount = float(m.group(1).replace(" ", ""))
            if amount >= 1000:
                return amount, "RUB"

    m = re.search(r"(\d+)\s*к\b", t)
    if m:
        return float(m.group(1)) * 1000, "RUB"
    return None, None


def _extract_destination_hint(text: str) -> str | None:
    """Короткие направления из типичных запросов «Бон Вояж»."""
    t = (text or "").lower()
    mapping = [
        ("хэйхэ", "Китай"),
        ("шанхай", "Китай"),
        ("бэйдайхэ", "Китай"),
        ("бейдайхэ", "Китай"),
        ("хэминху", "Китай"),
        ("дальян", "Китай"),
        ("китай", "Китай"),
        ("пхукет", "Таиланд"),
        ("таиланд", "Таиланд"),
        ("тайланд", "Таиланд"),
        ("антали", "Турция"),
        ("турци", "Турция"),
        ("фукуок", "Вьетнам"),
        ("нячанг", "Вьетнам"),
        ("вьетнам", "Вьетнам"),
        ("камчатк", "Россия"),
        ("космодром", "Россия"),
        ("росси", "Россия"),
        ("сочи", "Россия"),
        ("моск", "Россия"),
        ("оаэ", "ОАЭ"),
        ("дубай", "ОАЭ"),
        ("япони", "Япония"),
        ("египет", "Египет"),
    ]
    for key, dest in mapping:
        if key in t:
            return dest
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

    # Диапазон "10–17 декабря" / "1–8 сентября"
    m_dash = re.search(
        r"(\d{1,2})\s*[–\-]\s*(\d{1,2})\s+([а-яё]+)(?:\s+(\d{2,4}))?",
        user_message,
        re.IGNORECASE,
    )
    if m_dash:
        d1, d2, mon, y = m_dash.groups()
        mm = _month_from_word(mon)
        if mm:
            yy = _parse_year(y, ref_year)
            try:
                dt1 = _normalize_future(date(yy, mm, int(d1)))
                dt2 = _normalize_future(date(yy, mm, int(d2)))
                if dt2 >= dt1:
                    c["date_from"] = dt1.isoformat()
                    c["date_to"] = dt2.isoformat()
            except ValueError:
                pass

    # «с 5 августа на 10 дней»
    m_sd = re.search(
        r"с\s*(\d{1,2})\s+([а-яё]+)(?:\s+(\d{2,4}))?\s+на\s+(\d{1,2})\s+дн",
        um,
        re.IGNORECASE,
    )
    if m_sd:
        d1, mon, y, days_n = m_sd.groups()
        mm = _month_from_word(mon)
        if mm:
            yy = _parse_year(y, ref_year)
            try:
                dt1 = _normalize_future(date(yy, mm, int(d1)))
                c["date_from"] = dt1.isoformat()
                c["date_to"] = (dt1 + timedelta(days=int(days_n))).isoformat()
            except ValueError:
                pass

    # Имя клиента
    m_name = re.search(
        r"меня зовут\s+([а-яёa-z][а-яёa-z\-]{1,30})",
        um,
        re.IGNORECASE,
    )
    if m_name and not c.get("name"):
        name = m_name.group(1).strip().title()
        if name.lower() not in ("хочу", "хотел", "хотела", "ищу"):
            c["name"] = name

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

    # Бюджет
    budget, currency = _extract_budget(user_message)
    if budget is not None:
        c["budget"] = budget
        if currency:
            c["budget_currency"] = currency

    # Направление одним словом / в составе фразы
    if not c.get("destination"):
        dest_hint = _extract_destination_hint(user_message)
        if dest_hint:
            c["destination"] = dest_hint

    # Предпочтения (семейный, школьники, море)
    if not c.get("preferences"):
        prefs = []
        for word in ("семейн", "школьник", "море", "пляж", "экскурс", "лечебн", "шоп"):
            if word in um:
                prefs.append(word)
        if "благовещенск" in um:
            prefs.append("Благовещенск")
        if prefs:
            c["preferences"] = ", ".join(prefs)

    return c
