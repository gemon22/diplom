"""Случайные перелёты в БД — запасной источник цен для сборки турпакета."""

from __future__ import annotations

import random
from datetime import date, timedelta

FLIGHT_SOURCE = "catalog"

# Направление → (мин. цена ₽, макс. цена ₽) туда-обратно
DESTINATION_PRICES: dict[str, tuple[int, int]] = {
    "Китай": (18_000, 48_000),
    "Таиланд": (38_000, 82_000),
    "Турция": (32_000, 68_000),
    "Вьетнам": (42_000, 88_000),
    "Россия": (7_000, 28_000),
    "ОАЭ": (48_000, 98_000),
    "Япония": (58_000, 115_000),
    "Египет": (38_000, 72_000),
}

ORIGINS = ("Благовещенск", "Москва", "Хабаровск", "Москва")

AIRLINES = (
    "Аэрофлот",
    "S7 Airlines",
    "China Southern",
    "Turkish Airlines",
    "Emirates",
    "Vietnam Airlines",
    "Thai Airways",
    "Pegasus",
    "Qatar Airways",
    "Ural Airlines",
    "Nordwind",
)

# Сколько вариантов на каждое направление
FLIGHTS_PER_DESTINATION = 6


def generate_catalog_flights() -> list[dict]:
    """Генерирует список перелётов для save_flights()."""
    today = date.today()
    flights: list[dict] = []

    for dest, (lo, hi) in DESTINATION_PRICES.items():
        for _ in range(FLIGHTS_PER_DESTINATION):
            origin = random.choice(ORIGINS)
            dep_offset = random.randint(14, 300)
            trip_days = random.randint(5, 16)
            dep = today + timedelta(days=dep_offset)
            ret = dep + timedelta(days=trip_days)
            price = random.randint(lo, hi)
            # Благовещенск обычно дешевле в Китай
            if origin == "Благовещенск" and dest == "Китай":
                price = int(price * random.uniform(0.75, 0.95))
            elif origin == "Москва" and dest != "Россия":
                price = int(price * random.uniform(1.05, 1.25))

            flights.append(
                {
                    "origin": origin,
                    "destination": dest,
                    "departure_at": dep.isoformat(),
                    "return_at": ret.isoformat(),
                    "price": price,
                    "airline": random.choice(AIRLINES),
                    "source_site": FLIGHT_SOURCE,
                }
            )
    return flights


def db_rows_to_offers(rows: list[dict]) -> list[dict]:
    """Строки flights → формат для assemble_package."""
    offers = []
    for f in rows:
        offers.append(
            {
                "origin": f.get("from_city") or "",
                "destination": f.get("to_city") or "",
                "price": f.get("price"),
                "airline": f.get("airline") or "",
                "link": "",
                "source_site": f.get("source_site") or FLIGHT_SOURCE,
            }
        )
    return offers


def fetch_flights_from_db(db, destination: str, date_from: str, date_to: str, limit: int = 5) -> list[dict]:
    """Подбор перелётов из БД по направлению."""
    rows = db.get_flights(
        to_city=destination,
        departure_date=date_from or None,
        return_date=date_to or None,
        source_site=FLIGHT_SOURCE,
        limit=limit,
    )
    if not rows:
        rows = db.get_flights(
            to_city=destination,
            departure_date=date_from or None,
            return_date=date_to or None,
            limit=limit,
        )
    if not rows:
        rows = db.get_flights(
            to_city=destination,
            source_site=FLIGHT_SOURCE,
            limit=limit,
        )
    if not rows:
        rows = db.get_flights(to_city=destination, limit=limit)
    return db_rows_to_offers(rows)


def seed_catalog_flights(db, force: bool = False) -> int:
    """
    Заполняет таблицу flights случайными перелётами (source_site=catalog).
    force=True — пересоздать каталог.
    """
    expected = len(DESTINATION_PRICES) * FLIGHTS_PER_DESTINATION
    current = db.count_flights_by_source(FLIGHT_SOURCE)
    if current >= expected and not force:
        return current

    if force or current > 0:
        db.clear_flights_by_source(FLIGHT_SOURCE)

    flights = generate_catalog_flights()
    db.save_flights(flights)
    return len(flights)
