import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ai_service import ai
from budget_utils import format_budget_display, normalize_budget_rub
from catalog_context import normalize_collected_destination
from date_validation import validate_collected_dates
from flight_client import flights_client
from demo_mode import (
    DEMO_DISCLAIMER,
    attach_demo_flight,
    demo_activation_message,
    is_demo_mode,
    is_demo_trigger,
    mark_demo_tour,
    seed_demo_data,
)
from tour_links import apply_booking_links, is_valid_booking_url, resolve_agency_url, resolve_booking_url
from config import Config
from database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_INDEX = ROOT / "frontend" / "index.html"

app = FastAPI(title="Модуль генерации турпакета")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}


class ChatReq(BaseModel):
    session_id: Optional[str] = None
    message: str
    llm_provider: Optional[str] = None


class ChatResp(BaseModel):
    session_id: str
    response: str
    is_ready: bool = False
    tour_package: Optional[dict] = None
    llm_provider: Optional[str] = None
    llm_provider_label: Optional[str] = None
    llm_fallback: bool = False
    llm_tried: list[str] = Field(default_factory=list)


class LeadReq(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., min_length=6, max_length=50)
    email: Optional[str] = None
    message: Optional[str] = None
    session_id: Optional[str] = None
    tour_name: Optional[str] = None


class FlightSearchReq(BaseModel):
    destination: str
    date_from: str
    date_to: str
    origin_iata: Optional[str] = None
    provider: Optional[str] = None  # travelpayouts | amadeus | all


@app.on_event("startup")
async def startup():
    db = get_db()
    if Config.SEED_DEMO_ON_START:
        try:
            from demo_mode import seed_demo_data

            n = seed_demo_data(db)
            logger.info("Demo seed on start: %s records", n)
        except Exception as e:
            logger.warning("Demo seed failed: %s", e)


@app.get("/health")
async def health():
    try:
        db = get_db()
        db.connection.ping(reconnect=True, attempts=1, delay=0)
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "degraded", "database": str(e)}


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return HTMLResponse(FRONTEND_INDEX.read_text(encoding="utf-8"))


@app.get("/api/llm/providers")
async def llm_providers():
    return {"providers": ai.list_providers(), "default": Config.LLM_PROVIDER}


@app.get("/admin/stats")
async def stats():
    db = get_db()
    today = db.get_today_stats()
    return {
        "today_requests": today["requests_count"],
        "today_tours": today["tours_generated"],
        "active_sessions": len(sessions),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/reset")
async def reset_session(session_id: str):
    sessions.pop(session_id, None)
    return {"ok": True}


@app.post("/api/leads")
async def create_lead(req: LeadReq):
    db = get_db()
    lead_id = db.insert_lead(
        name=req.name.strip(),
        phone=req.phone.strip(),
        email=(req.email or "").strip() or None,
        message=(req.message or "").strip() or None,
        session_id=req.session_id,
        tour_name=(req.tour_name or "").strip() or None,
    )
    return {
        "ok": True,
        "lead_id": lead_id,
        "message": "Заявка принята. Менеджер свяжется с вами в ближайшее время.",
    }


@app.post("/api/flights/search")
async def flights_search(req: FlightSearchReq):
    db = get_db()
    offers = await flights_client.search_flights(
        destination=req.destination,
        date_from=req.date_from,
        date_to=req.date_to,
        origin_iata=req.origin_iata,
        currency="rub",
        provider=req.provider,
    )
    if offers:
        db.save_flights(offers[:10])
    return {
        "ok": bool(offers),
        "source": req.provider or Config.FLIGHTS_PROVIDER,
        "error": flights_client.last_error if not offers else None,
        "count": len(offers),
        "offers": offers[:10],
    }


@app.post("/api/chat", response_model=ChatResp)
async def chat(req: ChatReq):
    db = get_db()
    sid = req.session_id or str(uuid.uuid4())

    state = sessions.get(sid)
    if not state:
        state = db.get_session(sid) or {"collected": {}}
        sessions[sid] = state

    qid = db.log_query(sid, req.message)

    if is_demo_trigger(req.message):
        total = seed_demo_data(db)
        state["demo_mode"] = True
        state["collected"] = state.get("collected") or {}
        sessions[sid] = state
        db.save_session(sid, state)
        return ChatResp(
            session_id=sid,
            response=demo_activation_message(total),
            is_ready=False,
            tour_package=None,
        )

    provider = req.llm_provider or state.get("llm_provider") or Config.LLM_PROVIDER
    meta = {
        "llm_provider": None,
        "llm_provider_label": None,
        "llm_fallback": False,
        "llm_tried": [],
    }

    try:
        resp_text, new_state, ready, meta = await ai.process_message(
            req.message, state, provider=provider
        )
    except Exception as e:
        logger.error(f"ai.process_message crashed: {e}")
        resp_text = (
            "Извините, произошла ошибка. Пожалуйста, свяжитесь с нами по телефону +7(4162) 317-771."
        )
        new_state = state
        ready = False

    ready = bool(ready)
    sessions[sid] = new_state
    db.save_session(sid, new_state)

    tour = None
    if ready:
        params = new_state.get("collected", {})
        dates_ok, date_msg, params = validate_collected_dates(params)
        new_state["collected"] = params
        if not dates_ok:
            ready = False
            if date_msg:
                resp_text = date_msg
        if not ready:
            sessions[sid] = new_state
            db.save_session(sid, new_state)
            return ChatResp(
                session_id=sid,
                response=resp_text,
                is_ready=False,
                tour_package=None,
                llm_provider=meta.get("llm_provider"),
                llm_provider_label=meta.get("llm_provider_label"),
                llm_fallback=bool(meta.get("llm_fallback")),
                llm_tried=meta.get("llm_tried") or [],
            )

        demo = is_demo_mode(new_state)
        catalog_sample = db.get_all_hotels_sample(
            limit=50, source_site="demo" if demo else None
        )
        params = normalize_collected_destination(params, catalog_sample)
        new_state["collected"] = params

        dest = params.get("destination")
        city_pref = (params.get("city_preference") or "").strip().lower()
        budget_rub = normalize_budget_rub(params)
        hotels = db.get_hotels(
            destination=dest,
            max_price_rub=budget_rub,
            limit=15,
            source_site="demo" if demo else None,
        )
        if not hotels and dest:
            hotels = db.get_hotels(
                destination=dest,
                max_price_rub=None,
                limit=15,
                source_site="demo" if demo else None,
            )

        # Если пользователь явно просил Москву — не подсовываем туры по другой РФ.
        if city_pref == "москва":
            hotels = [
                h
                for h in hotels
                if "моск" in str(h.get("name", "")).lower()
                or "моск" in str(h.get("source_url", "")).lower()
            ]

        # Не отдаём пользователю "лучший тур" с нулевой ценой, если есть нормальные варианты.
        non_zero_hotels = [
            h for h in hotels if float(h.get("total_stay_price") or 0) > 0
        ]
        if non_zero_hotels:
            hotels = non_zero_hotels

        if hotels:
            used_llm = meta.get("llm_provider") or provider
            tour = await ai.generate_tour(params, hotels, provider=used_llm)

            if demo:
                flights = db.get_flights(
                    to_city=dest,
                    departure_date=params.get("date_from"),
                    return_date=params.get("date_to"),
                    source_site="demo",
                    limit=1,
                )
                tour = attach_demo_flight(tour, flights[0] if flights else None)
                tour = mark_demo_tour(tour)
                tour = apply_booking_links(tour, hotels, dest)
            else:
                offers = await flights_client.search_flights(
                    destination=dest or "",
                    date_from=params.get("date_from") or "",
                    date_to=params.get("date_to") or "",
                    origin_iata=None,
                    currency="rub",
                    provider=Config.FLIGHTS_PROVIDER,
                )
                if offers:
                    db.save_flights(offers[:10])
                    best = offers[0]
                    flight_info = f"{best.get('origin')} → {best.get('destination')}"
                    if best.get("airline"):
                        flight_info += f", {best.get('airline')}"
                    link = best.get("link")
                    if link:
                        if link.startswith("http"):
                            booking_link = link
                        else:
                            booking_link = f"https://www.aviasales.ru{link}"
                        tour.setdefault("booking_links", {})
                        tour["booking_links"]["self"] = booking_link
                    tour["flight"] = {
                        "estimated_price": best.get("price", 0),
                        "info": flight_info,
                    }
                    try:
                        hotel_price = float((tour.get("selected_hotel") or {}).get("price") or 0)
                        flight_price = float(best.get("price") or 0)
                        tour["total_price"] = hotel_price + flight_price
                    except (TypeError, ValueError):
                        pass

                self_link = (tour.get("booking_links") or {}).get("self") or ""
                if "aviasales" in self_link:
                    tour.setdefault("booking_links", {})["agency"] = resolve_agency_url()
                else:
                    tour = apply_booking_links(tour, hotels, dest)

            db.save_tour(qid, tour, tour.get("total_price", 0))
            tour["formatted"] = format_tour(tour, params, demo=demo)
        else:
            if city_pref == "москва":
                resp_text = (
                    "В текущем каталоге пока нет туров именно в Москву. "
                    "Могу предложить другие туры по России или вы можете оставить заявку менеджеру."
                )
            else:
                resp_text = (
                    f"По направлению «{dest}» в каталоге пока нет подходящих туров. "
                    "Попробуйте изменить бюджет или направление, либо оставьте заявку менеджеру."
                )
            ready = False

    return ChatResp(
        session_id=sid,
        response=resp_text,
        is_ready=ready,
        tour_package=tour,
        llm_provider=meta.get("llm_provider"),
        llm_provider_label=meta.get("llm_provider_label"),
        llm_fallback=bool(meta.get("llm_fallback")),
        llm_tried=meta.get("llm_tried") or [],
    )


def format_tour(tour, params, demo: bool = False):
    hotel = tour.get("selected_hotel", {})
    flight = tour.get("flight", {})
    links = tour.setdefault("booking_links", {})
    self_link = links.get("self", "#")
    if not is_valid_booking_url(self_link):
        self_link = resolve_booking_url(hotel, params.get("destination"))
    agency_link = resolve_agency_url()
    links["self"] = self_link
    links["agency"] = agency_link
    tour["booking_url"] = self_link
    budget_str = format_budget_display(params)

    def rub(v):
        try:
            return f"{float(v):,.0f}".replace(",", " ") + " ₽"
        except (TypeError, ValueError):
            return "—"

    demo_note = ""
    if demo or tour.get("is_demo"):
        demo_note = (
            '<p style="color:#856404;background:#fff3cd;padding:10px 14px;border-radius:8px;">'
            f"{DEMO_DISCLAIMER}</p>"
        )

    return f"""
<p><strong>Тур: {params.get('destination', '')}</strong></p>
<p>📅 {params.get('date_from')} – {params.get('date_to')}</p>
<p>💰 Ваш бюджет: {budget_str}</p>
<p>🏨 <strong>{hotel.get('name', '')}</strong> — {rub(hotel.get('price', 0))}</p>
<p>✈️ {flight.get('info', 'перелёт')} — {rub(flight.get('estimated_price', 0))}</p>
<p><strong>Итого: {rub(tour.get('total_price', 0))}</strong></p>
{demo_note}
<p>{tour.get('recommendation_text', '')}</p>
<p>
  <a href="{self_link}" target="_blank" rel="noopener">Купить самостоятельно</a>
  &nbsp;|&nbsp;
  <a href="{agency_link}" target="_blank" rel="noopener">Страница турфирмы</a>
</p>
"""


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
