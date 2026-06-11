"""Проверка и подстановка рабочих ссылок на сайт туроператора."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from config import Config

# Страницы, которые существуют на bon-voyage28.ru (проверено)
DESTINATION_CATALOG_URLS = {
    "Китай": "https://bon-voyage28.ru/tury/",
    "Россия": "https://bon-voyage28.ru/tury/",
    "Таиланд": "https://bon-voyage28.ru/tury/",
    "Турция": "https://bon-voyage28.ru/tury/",
    "Вьетнам": "https://bon-voyage28.ru/tury/",
    "Япония": "https://bon-voyage28.ru/tury/",
    "ОАЭ": "https://bon-voyage28.ru/tury/",
    "Египет": "https://bon-voyage28.ru/tury/",
}

PLACEHOLDER_MARKERS = ("/demo/", "example.com", "localhost", "127.0.0.1")

# Тестовые slug из demo_mode — на сайте их нет (404)
_FAKE_TOUR_SLUG = re.compile(
    r"/tury/(china|thai|turkey|viet|russia|japan|uae)-\d+/?$",
    re.I,
)

# Страницы, которые отдают 404
_DEAD_PATHS = ("/contacts", "/contacts/", "/kontakty", "/kontakty/")


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
        # Aviasales и другие внешние агрегаторы — допустимы для «Купить самостоятельно»
        return host.endswith("aviasales.ru") or "aviasales" in host
    path = (parsed.path or "/").rstrip("/") or "/"
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
    return Config.SITE_PRIMARY_URL.rstrip("/") + "/"


def resolve_booking_url(hotel: dict | None, destination: str | None = None) -> str:
    """Ссылка «Купить самостоятельно» — только на существующие страницы."""
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
    return Config.SITE_PRIMARY_URL.rstrip("/") + "/"


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
