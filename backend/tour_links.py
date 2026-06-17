"""Проверка и подстановка рабочих ссылок на сайт туроператора."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from config import Config

# Реальные страницы каталога (проверено: /tury — пустая страница!)
DESTINATION_CATALOG_URLS = {
    "Китай": "https://bon-voyage28.ru/country/china/tury-cn/",
    "Россия": "https://bon-voyage28.ru/country/russia/tury/tury-po-rossii/",
    "Таиланд": "https://bon-voyage28.ru/country/thailand",
    "Турция": "https://bon-voyage28.ru/country/turkey",
    "Вьетнам": "https://bon-voyage28.ru/country/vietnam",
    "ОАЭ": "https://bon-voyage28.ru/country/uae",
    "Япония": "https://bon-voyage28.ru/",
    "Египет": "https://bon-voyage28.ru/",
    "Корея": "https://bon-voyage28.ru/",
    "Греция": "https://bon-voyage28.ru/",
    "Испания": "https://bon-voyage28.ru/",
    "Италия": "https://bon-voyage28.ru/",
}

SITE_HOME = "https://bon-voyage28.ru/"

PLACEHOLDER_MARKERS = ("/demo/", "example.com", "localhost", "127.0.0.1")

# Пустая / битая страница каталога
_GENERIC_CATALOG_PATHS = frozenset({"/tury", "/tury/", "/tours", "/tours/"})

_FAKE_TOUR_SLUG = re.compile(
    r"/tury/(china|thai|turkey|viet|russia|japan|uae)-\d+/?$",
    re.I,
)

_DEAD_PATHS = ("/contacts", "/contacts/", "/kontakty", "/kontakty/")


def _path_of(url: str) -> str:
    parsed = urlparse(url.lower().strip())
    path = (parsed.path or "/").rstrip("/") or "/"
    return path


def is_generic_catalog_url(url: str | None) -> bool:
    if not url:
        return True
    return _path_of(url) in _GENERIC_CATALOG_PATHS


def is_valid_booking_url(url: str | None) -> bool:
    if not url or url.strip() in ("", "#"):
        return False
    low = url.lower().strip()
    if any(m in low for m in PLACEHOLDER_MARKERS):
        return False
    parsed = urlparse(low)
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.netloc.lower()
    if not host:
        return False
    allowed = ("bon-voyage28.ru", "bonvoyage28.ru", "www.bon-voyage28.ru")
    if not any(host == d or host.endswith("." + d) for d in allowed):
        return host.endswith("aviasales.ru") or "aviasales" in host
    path = _path_of(low)
    if path in _GENERIC_CATALOG_PATHS:
        return False
    if path in _DEAD_PATHS or path + "/" in _DEAD_PATHS:
        return False
    if _FAKE_TOUR_SLUG.search(parsed.path or ""):
        return False
    return True


def normalize_external_url(url: str) -> str:
    url = url.strip()
    base = Config.SITE_PRIMARY_URL.rstrip("/")
    if url.startswith("http"):
        return url
    return f"{base}/{url.lstrip('/')}"


def catalog_url_for_destination(destination: str | None) -> str:
    dest = (destination or "").strip()
    if dest in DESTINATION_CATALOG_URLS:
        return DESTINATION_CATALOG_URLS[dest]
    return SITE_HOME


def resolve_booking_url(hotel: dict | None, destination: str | None = None) -> str:
    """Ссылка на тур — конкретная страница с сайта, не пустой /tury."""
    h = hotel or {}
    raw = h.get("source_url") or ""
    if is_valid_booking_url(raw):
        return normalize_external_url(raw)
    dest = destination or h.get("destination")
    return catalog_url_for_destination(dest)


def resolve_agency_url() -> str:
    url = Config.AGENCY_CONTACT_URL or Config.SITE_PRIMARY_URL
    if is_valid_booking_url(url):
        return normalize_external_url(url)
    return SITE_HOME


def find_hotel_in_catalog(hotels_data: list, tour: dict) -> dict:
    sel_name = ((tour.get("selected_hotel") or {}).get("name") or "").strip().lower()
    if sel_name:
        for h in hotels_data:
            name = (h.get("name") or "").strip().lower()
            if name == sel_name or sel_name in name or name in sel_name:
                return h
    return hotels_data[0] if hotels_data else {}


def apply_booking_links(tour: dict, hotels_data: list, destination: str | None = None) -> dict:
    hotel = find_hotel_in_catalog(hotels_data, tour)
    dest = destination or hotel.get("destination") or (tour.get("selected_hotel") or {}).get(
        "description"
    )
    links = tour.setdefault("booking_links", {})
    links["self"] = resolve_booking_url(hotel, dest)
    links["agency"] = resolve_agency_url()
    tour["booking_url"] = links["self"]
    return tour


def fix_stale_urls_in_db(db) -> int:
    """Обновляет в БД ссылки на /tury и фейковые slug → рабочие страницы."""
    cursor = db.connection.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT id, destination, source_url FROM hotels
        WHERE source_url LIKE '%/tury%'
           OR source_url LIKE '%china-%'
           OR source_url LIKE '%thai-%'
           OR source_url LIKE '%turkey-%'
           OR source_url LIKE '%viet-%'
           OR source_url LIKE '%russia-%'
           OR source_url LIKE '%japan-%'
           OR source_url LIKE '%uae-%'
        """
    )
    rows = cursor.fetchall()
    updated = 0
    for row in rows:
        url = row.get("source_url") or ""
        if is_valid_booking_url(url):
            continue
        new_url = catalog_url_for_destination(row.get("destination"))
        cursor.execute(
            "UPDATE hotels SET source_url = %s WHERE id = %s",
            (new_url, row["id"]),
        )
        updated += 1
    db.connection.commit()
    cursor.close()
    return updated
