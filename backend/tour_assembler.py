"""Динамическая сборка турпакета: перелёт и проживание отдельно + готовые туры из каталога."""

from __future__ import annotations

from datetime import datetime

from budget_utils import format_budget_display, normalize_budget_rub
from demo_mode import DEMO_DISCLAIMER
from tour_links import is_valid_booking_url, resolve_agency_url, resolve_booking_url


def _rub(value) -> str:
    try:
        return f"{float(value):,.0f}".replace(",", " ") + " ₽"
    except (TypeError, ValueError):
        return "—"


def _float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _nights(date_from: str | None, date_to: str | None) -> int:
    try:
        d1 = datetime.strptime(date_from or "", "%Y-%m-%d")
        d2 = datetime.strptime(date_to or "", "%Y-%m-%d")
        return max(1, (d2 - d1).days)
    except (TypeError, ValueError):
        return 7


def _accommodation_price(row: dict, nights: int) -> float:
    per_night = _float(row.get("price_per_night"))
    total = _float(row.get("total_stay_price"))
    if per_night > 0:
        return per_night * nights
    return total


def _flight_from_offer(offer: dict) -> dict:
    info = f"{offer.get('origin', '')} → {offer.get('destination', '')}"
    if offer.get("airline"):
        info += f", {offer.get('airline')}"
    link = offer.get("link") or ""
    if link and not link.startswith("http"):
        link = f"https://www.aviasales.ru{link}"
    return {
        "price": _float(offer.get("price")),
        "info": info,
        "airline": offer.get("airline") or "",
        "from_city": offer.get("origin") or "",
        "to_city": offer.get("destination") or "",
        "link": link,
        "source": offer.get("source_site") or "api",
    }


def _flight_from_db(row: dict) -> dict:
    info = f"{row.get('from_city', '')} → {row.get('to_city', '')}"
    if row.get("airline"):
        info += f", {row.get('airline')}"
    return {
        "price": _float(row.get("price")),
        "info": info,
        "airline": row.get("airline") or "",
        "from_city": row.get("from_city") or "",
        "to_city": row.get("to_city") or "",
        "link": "",
        "source": row.get("source_site") or "db",
    }


def _accommodation_from_row(row: dict, nights: int, destination: str | None) -> dict:
    price = _accommodation_price(row, nights)
    link = resolve_booking_url(row, destination or row.get("destination"))
    return {
        "name": row.get("name") or "Проживание",
        "price": price,
        "price_per_night": _float(row.get("price_per_night")),
        "nights": nights,
        "destination": row.get("destination") or destination or "",
        "amenities": row.get("amenities") or "",
        "rating": _float(row.get("rating")),
        "link": link,
    }


def _ready_tour_from_row(row: dict, destination: str | None, budget_rub: float) -> dict:
    price = _float(row.get("total_stay_price"))
    link = resolve_booking_url(row, destination or row.get("destination"))
    if price <= budget_rub:
        fit = "в рамках бюджета"
    elif budget_rub > 0 and price <= budget_rub * 1.15:
        fit = "чуть выше бюджета"
    else:
        fit = "премиум-вариант"
    return {
        "name": row.get("name") or "Тур",
        "price": price,
        "destination": row.get("destination") or destination or "",
        "amenities": row.get("amenities") or "",
        "rating": _float(row.get("rating")),
        "link": link,
        "fit_note": fit,
    }


def pick_modular_accommodation(
    hotels: list[dict], nights: int, exclude_names: set[str] | None = None
) -> dict | None:
    """Проживание для раздельной сборки — лучшее соотношение цена/ночь."""
    exclude = exclude_names or set()
    candidates = [h for h in hotels if (h.get("name") or "") not in exclude]
    if not candidates:
        return None

    def score(row: dict) -> float:
        per_night = _float(row.get("price_per_night"))
        if per_night > 0:
            return per_night
        total = _float(row.get("total_stay_price"))
        return total / nights if total > 0 else 999_999_999

    best = min(candidates, key=score)
    return best


def pick_ready_tours(
    hotels: list[dict],
    destination: str | None,
    budget_rub: float,
    count: int = 3,
    exclude_names: set[str] | None = None,
) -> list[dict]:
    """Готовые туры из каталога — до count вариантов по бюджету."""
    exclude = exclude_names or set()
    seen: set[str] = set()
    items: list[dict] = []

    def budget_distance(row: dict) -> float:
        price = _float(row.get("total_stay_price"))
        if price <= 0:
            return 999_999_999
        if budget_rub <= 0:
            return price
        if price <= budget_rub:
            return budget_rub - price
        return price - budget_rub + 1_000_000

    for row in sorted(hotels, key=budget_distance):
        name = (row.get("name") or "").strip()
        if not name or name in exclude or name in seen:
            continue
        if _float(row.get("total_stay_price")) <= 0:
            continue
        seen.add(name)
        items.append(_ready_tour_from_row(row, destination, budget_rub))
        if len(items) >= count:
            break
    return items


def assemble_package(
    params: dict,
    hotels: list[dict],
    flight_offers: list[dict] | None = None,
    demo: bool = False,
) -> dict:
    """
    Формирует турпакет двух типов:
    - modular: перелёт + проживание (отдельные компоненты);
    - ready_tours: готовые туры из каталога «Бон Вояж».
    """
    destination = params.get("destination") or ""
    budget_rub = normalize_budget_rub(params)
    nights = _nights(params.get("date_from"), params.get("date_to"))
    offers = flight_offers or []

    flight = _flight_from_offer(offers[0]) if offers else {
        "price": 0,
        "info": "Уточните у менеджера",
        "airline": "",
        "from_city": "",
        "to_city": destination,
        "link": "",
        "source": "none",
    }

    acc_row = pick_modular_accommodation(hotels, nights)
    accommodation = (
        _accommodation_from_row(acc_row, nights, destination) if acc_row else None
    )

    exclude = {accommodation["name"]} if accommodation else set()
    ready_tours = pick_ready_tours(
        hotels, destination, budget_rub, count=3, exclude_names=exclude
    )

    modular_total = _float(flight.get("price"))
    if accommodation:
        modular_total += _float(accommodation.get("price"))

    agency_link = resolve_agency_url()
    recommendation = _build_recommendation(
        destination, budget_rub, modular_total, accommodation, flight, ready_tours
    )

    package = {
        "assembly_mode": "dual",
        "destination": destination,
        "date_from": params.get("date_from"),
        "date_to": params.get("date_to"),
        "nights": nights,
        "budget_rub": budget_rub,
        "currency": "RUB",
        "modular": {
            "flight": flight,
            "accommodation": accommodation,
            "total_price": modular_total,
        },
        "ready_tours": ready_tours,
        "recommendation_text": recommendation,
        "booking_links": {
            "agency": agency_link,
            "flight": flight.get("link") or agency_link,
            "accommodation": (accommodation or {}).get("link") or agency_link,
        },
        "is_demo": demo,
        # Совместимость со старым форматом / заявками
        "total_price": modular_total,
        "selected_hotel": {
            "name": (accommodation or {}).get("name", ""),
            "price": (accommodation or {}).get("price", 0),
            "description": destination,
        },
        "flight": {
            "estimated_price": flight.get("price", 0),
            "info": flight.get("info", ""),
        },
    }
    if ready_tours:
        package["booking_links"]["self"] = ready_tours[0].get("link") or agency_link
    elif accommodation:
        package["booking_links"]["self"] = accommodation.get("link") or agency_link
    else:
        package["booking_links"]["self"] = agency_link

    return package


def attach_db_flight(package: dict, flight_row: dict | None) -> dict:
    if not flight_row:
        return package
    flight = _flight_from_db(flight_row)
    package["modular"]["flight"] = flight
    acc_price = _float((package["modular"].get("accommodation") or {}).get("price"))
    package["modular"]["total_price"] = _float(flight.get("price")) + acc_price
    package["total_price"] = package["modular"]["total_price"]
    package["flight"] = {
        "estimated_price": flight.get("price", 0),
        "info": flight.get("info", ""),
    }
    if flight.get("link"):
        package["booking_links"]["flight"] = flight["link"]
    return package


def _build_recommendation(
    destination: str,
    budget_rub: float,
    modular_total: float,
    accommodation: dict | None,
    flight: dict,
    ready_tours: list[dict],
) -> str:
    parts = [f"Направление: {destination}."]
    if accommodation and flight.get("price"):
        parts.append(
            f"Раздельная сборка: перелёт {_rub(flight['price'])} + "
            f"проживание «{accommodation['name']}» {_rub(accommodation['price'])} "
            f"= {_rub(modular_total)}."
        )
    if ready_tours:
        names = ", ".join(f"«{t['name']}»" for t in ready_tours[:2])
        parts.append(f"Готовые туры из каталога: {names}.")
    if budget_rub > 0 and modular_total > budget_rub:
        parts.append("Сборка чуть выше бюджета — менеджер поможет подобрать альтернативу.")
    elif budget_rub > 0 and modular_total <= budget_rub:
        parts.append("Раздельная сборка укладывается в ваш бюджет.")
    return " ".join(parts)


def format_package_html(package: dict, params: dict, demo: bool = False) -> str:
    """HTML-карточка: блок раздельной сборки + блок готовых туров."""
    dest = package.get("destination") or params.get("destination", "")
    budget_str = format_budget_display(params)
    modular = package.get("modular") or {}
    flight = modular.get("flight") or {}
    accommodation = modular.get("accommodation")
    ready_tours = package.get("ready_tours") or []
    agency = resolve_agency_url()

    demo_note = ""
    if demo or package.get("is_demo"):
        demo_note = (
            '<p style="color:#856404;background:#fff3cd;padding:10px 14px;border-radius:8px;margin-top:10px;">'
            f"{DEMO_DISCLAIMER}</p>"
        )

    flight_link = flight.get("link") or agency
    flight_buy = (
        f'<a href="{flight_link}" target="_blank" rel="noopener">Купить билет</a>'
        if is_valid_booking_url(flight_link) or "aviasales" in flight_link
        else f'<a href="{agency}" target="_blank" rel="noopener">Уточнить у менеджера</a>'
    )

    acc_block = ""
    if accommodation:
        acc_link = accommodation.get("link") or agency
        acc_block = f"""
        <p>🏨 <strong>Проживание:</strong> {accommodation.get('name', '')}</p>
        <p style="margin-left:12px;color:#475569;">
          {accommodation.get('nights', '')} ноч. · {_rub(accommodation.get('price', 0))}
          · <a href="{acc_link}" target="_blank" rel="noopener">Подробнее на сайте</a>
        </p>"""

    modular_block = f"""
    <div class="pkg-section pkg-modular">
      <h4>📦 Сборка по отдельности</h4>
      <p style="color:#64748b;font-size:0.85rem;">Перелёт и проживание подбираются независимо</p>
      <p>✈️ <strong>Перелёт:</strong> {flight.get('info', '—')} — {_rub(flight.get('price', 0))}</p>
      <p style="margin-left:12px;">{flight_buy}</p>
      {acc_block}
      <p style="margin-top:10px;"><strong>Итого сборка: {_rub(modular.get('total_price', 0))}</strong></p>
    </div>"""

    ready_items = ""
    for i, tour in enumerate(ready_tours, 1):
        link = tour.get("link") or agency
        ready_items += f"""
        <li style="margin-bottom:10px;">
          <strong>{i}. {tour.get('name', '')}</strong> — {_rub(tour.get('price', 0))}
          <span style="color:#64748b;font-size:0.85rem;"> ({tour.get('fit_note', '')})</span><br>
          <a href="{link}" target="_blank" rel="noopener">Страница тура на bon-voyage28.ru</a>
        </li>"""

    ready_block = ""
    if ready_tours:
        ready_block = f"""
    <div class="pkg-section pkg-ready">
      <h4>🎫 Готовые туры из каталога</h4>
      <p style="color:#64748b;font-size:0.85rem;">Пакеты «под ключ» от туроператора «Бон Вояж»</p>
      <ol style="margin:8px 0 0 18px;padding:0;">{ready_items}</ol>
    </div>"""
    else:
        ready_block = """
    <div class="pkg-section pkg-ready">
      <h4>🎫 Готовые туры</h4>
      <p style="color:#64748b;">По этому направлению готовые пакеты уточняйте у менеджера.</p>
    </div>"""

    return f"""
<div class="tour-package">
  <p><strong>{dest}</strong> · 📅 {params.get('date_from')} – {params.get('date_to')}</p>
  <p>💰 Ваш бюджет: {budget_str}</p>
  {modular_block}
  {ready_block}
  <p style="margin-top:12px;color:#475569;font-size:0.9rem;">{package.get('recommendation_text', '')}</p>
  <p style="margin-top:8px;">
    <a href="{agency}" target="_blank" rel="noopener">Заявка менеджеру «Бон Вояж»</a>
  </p>
  {demo_note}
</div>"""
