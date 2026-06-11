"""Режим демонстрации: тестовые отели и перелёты в БД, диалог через LLM как обычно."""

from __future__ import annotations

import re
from datetime import date, timedelta

from tour_links import catalog_url_for_destination

DEMO_SOURCE = "demo"

DEMO_DISCLAIMER = (
    "⚠️ Турпакет сформирован на тестовых данных (демонстрационный режим). "
    "Цены, перелёты и описания не являются реальными предложениями турфирмы."
)

DEMO_HOTELS: list[dict] = [
    {"name": "Тур «Жемчужина Китая» — Шанхай", "destination": "Китай", "price_per_night": 8500, "total_stay_price": 59500, "amenities": "экскурсии, трансфер", "rating": 4.7, "source_url": "https://bon-voyage28.ru/tury/china-1"},
    {"name": "Тур «Хэйхэ — выходные»", "destination": "Китай", "price_per_night": 6200, "total_stay_price": 24800, "amenities": "шоп-тур, трансфер", "rating": 4.5, "source_url": "https://bon-voyage28.ru/tury/china-2"},
    {"name": "Тур «Пекин — история и культура»", "destination": "Китай", "price_per_night": 9100, "total_stay_price": 72800, "amenities": "экскурсии, завтраки", "rating": 4.8, "source_url": "https://bon-voyage28.ru/tury/china-3"},
    {"name": "Тур «Паттайя — море и отдых»", "destination": "Таиланд", "price_per_night": 7800, "total_stay_price": 54600, "amenities": "пляж, трансфер", "rating": 4.6, "source_url": "https://bon-voyage28.ru/tury/thai-1"},
    {"name": "Тур «Пхукет All Inclusive»", "destination": "Таиланд", "price_per_night": 11200, "total_stay_price": 78400, "amenities": "всё включено", "rating": 4.9, "source_url": "https://bon-voyage28.ru/tury/thai-2"},
    {"name": "Тур «Бангкок — город контрастов»", "destination": "Таиланд", "price_per_night": 6900, "total_stay_price": 48300, "amenities": "экскурсии", "rating": 4.4, "source_url": "https://bon-voyage28.ru/tury/thai-3"},
    {"name": "Тур «Анталия — семейный отдых»", "destination": "Турция", "price_per_night": 7400, "total_stay_price": 51800, "amenities": "бассейн, трансфер", "rating": 4.5, "source_url": "https://bon-voyage28.ru/tury/turkey-1"},
    {"name": "Тур «Стамбул — две столицы»", "destination": "Турция", "price_per_night": 8800, "total_stay_price": 61600, "amenities": "экскурсии, завтраки", "rating": 4.7, "source_url": "https://bon-voyage28.ru/tury/turkey-2"},
    {"name": "Тур «Нячанг — пляжный»", "destination": "Вьетнам", "price_per_night": 6500, "total_stay_price": 45500, "amenities": "море, трансфер", "rating": 4.3, "source_url": "https://bon-voyage28.ru/tury/viet-1"},
    {"name": "Тур «Фукуок — тропики»", "destination": "Вьетнам", "price_per_night": 9800, "total_stay_price": 68600, "amenities": "курорт", "rating": 4.6, "source_url": "https://bon-voyage28.ru/tury/viet-2"},
    {"name": "Тур «Сочи — Черное море»", "destination": "Россия", "price_per_night": 5200, "total_stay_price": 36400, "amenities": "море, экскурсии", "rating": 4.4, "source_url": "https://bon-voyage28.ru/tury/russia-1"},
    {"name": "Тур «Москва — классика»", "destination": "Россия", "price_per_night": 6100, "total_stay_price": 42700, "amenities": "экскурсии, отель 4*", "rating": 4.5, "source_url": "https://bon-voyage28.ru/tury/russia-2"},
    {"name": "Тур «Камчатка — дикая природа»", "destination": "Россия", "price_per_night": 14500, "total_stay_price": 101500, "amenities": "экскурсии, гид", "rating": 4.9, "source_url": "https://bon-voyage28.ru/tury/russia-3"},
    {"name": "Тур «Токио — современный мегаполис»", "destination": "Япония", "price_per_night": 13200, "total_stay_price": 92400, "amenities": "экскурсии, JR Pass", "rating": 4.8, "source_url": "https://bon-voyage28.ru/tury/japan-1"},
    {"name": "Тур «Дубай — luxury weekend»", "destination": "ОАЭ", "price_per_night": 15800, "total_stay_price": 94800, "amenities": "отель 5*, трансфер", "rating": 4.7, "source_url": "https://bon-voyage28.ru/tury/uae-1"},
]

_DEMO_FLIGHT_BASE = date.today() + timedelta(days=30)

DEMO_FLIGHTS: list[dict] = [
    {"from_city": "Благовещенск", "to_city": "Китай", "departure_date": _DEMO_FLIGHT_BASE, "return_date": _DEMO_FLIGHT_BASE + timedelta(days=7), "price": 28500, "airline": "Aeroflot"},
    {"from_city": "Благовещенск", "to_city": "Китай", "departure_date": _DEMO_FLIGHT_BASE + timedelta(days=3), "return_date": _DEMO_FLIGHT_BASE + timedelta(days=10), "price": 31200, "airline": "S7 Airlines"},
    {"from_city": "Благовещенск", "to_city": "Китай", "departure_date": _DEMO_FLIGHT_BASE + timedelta(days=5), "return_date": _DEMO_FLIGHT_BASE + timedelta(days=12), "price": 26800, "airline": "China Southern"},
    {"from_city": "Москва", "to_city": "Таиланд", "departure_date": _DEMO_FLIGHT_BASE, "return_date": _DEMO_FLIGHT_BASE + timedelta(days=10), "price": 45600, "airline": "Thai Airways"},
    {"from_city": "Москва", "to_city": "Таиланд", "departure_date": _DEMO_FLIGHT_BASE + timedelta(days=7), "return_date": _DEMO_FLIGHT_BASE + timedelta(days=17), "price": 42300, "airline": "Emirates"},
    {"from_city": "Москва", "to_city": "Турция", "departure_date": _DEMO_FLIGHT_BASE, "return_date": _DEMO_FLIGHT_BASE + timedelta(days=8), "price": 38900, "airline": "Turkish Airlines"},
    {"from_city": "Москва", "to_city": "Турция", "departure_date": _DEMO_FLIGHT_BASE + timedelta(days=4), "return_date": _DEMO_FLIGHT_BASE + timedelta(days=11), "price": 36500, "airline": "Pegasus"},
    {"from_city": "Москва", "to_city": "Вьетнам", "departure_date": _DEMO_FLIGHT_BASE, "return_date": _DEMO_FLIGHT_BASE + timedelta(days=9), "price": 51200, "airline": "Vietnam Airlines"},
    {"from_city": "Москва", "to_city": "Вьетнам", "departure_date": _DEMO_FLIGHT_BASE + timedelta(days=6), "return_date": _DEMO_FLIGHT_BASE + timedelta(days=15), "price": 49800, "airline": "Qatar Airways"},
    {"from_city": "Москва", "to_city": "Россия", "departure_date": _DEMO_FLIGHT_BASE, "return_date": _DEMO_FLIGHT_BASE + timedelta(days=5), "price": 12400, "airline": "Аэрофлот"},
    {"from_city": "Москва", "to_city": "Россия", "departure_date": _DEMO_FLIGHT_BASE + timedelta(days=2), "return_date": _DEMO_FLIGHT_BASE + timedelta(days=7), "price": 15800, "airline": "S7 Airlines"},
    {"from_city": "Москва", "to_city": "Япония", "departure_date": _DEMO_FLIGHT_BASE, "return_date": _DEMO_FLIGHT_BASE + timedelta(days=9), "price": 67800, "airline": "JAL"},
    {"from_city": "Москва", "to_city": "ОАЭ", "departure_date": _DEMO_FLIGHT_BASE, "return_date": _DEMO_FLIGHT_BASE + timedelta(days=6), "price": 54200, "airline": "Flydubai"},
    {"from_city": "Москва", "to_city": "Египет", "departure_date": _DEMO_FLIGHT_BASE, "return_date": _DEMO_FLIGHT_BASE + timedelta(days=8), "price": 41500, "airline": "EgyptAir"},
    {"from_city": "Благовещенск", "to_city": "Египет", "departure_date": _DEMO_FLIGHT_BASE + timedelta(days=10), "return_date": _DEMO_FLIGHT_BASE + timedelta(days=18), "price": 58900, "airline": "Aeroflot"},
]


def normalize_trigger_text(text: str) -> str:
    t = (text or "").lower().replace("ё", "е")
    t = re.sub(r"\s+", " ", t).strip()
    t = t.replace("пререйдем", "перейдем").replace("перейдём", "перейдем")
    return t


def is_demo_trigger(user_message: str) -> bool:
    t = normalize_trigger_text(user_message)
    if "режим демонстрации" in t:
        return True
    if "демонстрац" in t and ("перейдем" in t or "давай" in t or "включ" in t):
        return True
    return False


def is_demo_mode(state: dict | None) -> bool:
    return bool(state and state.get("demo_mode"))


def demo_activation_message(records: int) -> str:
    return (
        f"✅ Режим демонстрации включён. Загружено {records} тестовых записей "
        f"({len(DEMO_HOTELS)} туров и {len(DEMO_FLIGHTS)} перелётов).\n\n"
        "Дальше диалог идёт как обычно: укажите направление, даты и бюджет. "
        "В финальном описании тура будет указано, что использованы тестовые данные."
    )


def mark_demo_tour(tour: dict) -> dict:
    tour["is_demo"] = True
    return tour


def attach_demo_flight(tour: dict, flight: dict | None) -> dict:
    if not flight:
        return tour
    fp = float(flight.get("price") or 0)
    info = f"{flight.get('from_city')} → {flight.get('to_city')}"
    if flight.get("airline"):
        info += f", {flight.get('airline')}"
    tour["flight"] = {"estimated_price": fp, "info": info}
    try:
        hotel_price = float((tour.get("selected_hotel") or {}).get("price") or 0)
        tour["total_price"] = hotel_price + fp
    except (TypeError, ValueError):
        pass
    return tour


def seed_demo_data(db) -> int:
    """Загружает 30 тестовых записей (15 отелей + 15 перелётов), если их ещё нет."""
    existing = db.count_demo_records()
    if existing >= len(DEMO_HOTELS) + len(DEMO_FLIGHTS):
        return existing

    db.clear_demo_data()
    hotels = [
        {
            **h,
            "source_site": DEMO_SOURCE,
            "source_url": catalog_url_for_destination(h.get("destination")),
        }
        for h in DEMO_HOTELS
    ]
    db.insert_hotels(hotels)

    flights = []
    for f in DEMO_FLIGHTS:
        flights.append(
            {
                "origin": f["from_city"],
                "destination": f["to_city"],
                "departure_at": f["departure_date"].isoformat(),
                "return_at": f["return_date"].isoformat(),
                "price": f["price"],
                "airline": f["airline"],
                "source_site": DEMO_SOURCE,
            }
        )
    db.save_flights(flights)
    return len(hotels) + len(flights)
