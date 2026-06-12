import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from ai_service import ai
from budget_utils import normalize_budget_rub
from catalog_context import normalize_collected_destination
from date_validation import validate_collected_dates
from flight_client import flights_client
from demo_mode import (
    demo_activation_message,
    is_demo_mode,
    is_demo_trigger,
    mark_demo_tour,
    seed_demo_data,
)
from tour_assembler import assemble_package, attach_db_flight, format_package_html
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
    try:
        from dialog_training import training_stats

        s = training_stats()
        logger.info(
            "Dialog training loaded: %s examples (%s ready)",
            s.get("total_examples"),
            s.get("ready_examples"),
        )
    except Exception as e:
        logger.warning("Dialog training not loaded: %s", e)

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


SITE = Config.SITE_PRIMARY_URL.rstrip("/")


def _redirect(url: str):
    return RedirectResponse(url=url, status_code=302)


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return HTMLResponse(FRONTEND_INDEX.read_text(encoding="utf-8"))


@app.get("/tury")
@app.get("/tury/")
async def redirect_tury():
    return _redirect(f"{SITE}/tury")


@app.get("/tours")
@app.get("/tours/")
async def redirect_china_tours():
    return _redirect(f"{SITE}/country/china/tury-cn/")


@app.get("/goryashchie-tury")
@app.get("/goryashchie-tury/")
async def redirect_specials():
    return _redirect(f"{SITE}/news/")


@app.get("/kontakty")
@app.get("/kontakty/")
@app.get("/contacts")
@app.get("/contacts/")
async def redirect_contacts():
    return _redirect(f"{SITE}/company/contacts")


@app.get("/api/llm/providers")
async def llm_providers():
    return {"providers": ai.list_providers(), "default": Config.LLM_PROVIDER}


@app.get("/api/training/stats")
async def training_stats_api():
    from dialog_training import training_stats
    from training_loader import validate_all_examples

    try:
        db = get_db()
        rows = db.get_all_hotels_sample(limit=50)
        dests = list({r.get("destination") for r in rows if r.get("destination")})
    except Exception:
        dests = None
    validation = validate_all_examples(catalog_dests=dests)
    return {
        **training_stats(),
        "validation_avg_pct": validation.get("avg_score_pct", 0),
        "validation_count": validation.get("count", 0),
    }


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
            flight_offers: list[dict] = []

            if demo:
                demo_flights = db.get_flights(
                    to_city=dest,
                    departure_date=params.get("date_from"),
                    return_date=params.get("date_to"),
                    source_site="demo",
                    limit=3,
                )
                flight_offers = [
                    {
                        "origin": f.get("from_city"),
                        "destination": f.get("to_city"),
                        "price": f.get("price"),
                        "airline": f.get("airline"),
                        "link": "",
                        "source_site": "demo",
                    }
                    for f in demo_flights
                ]
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
                    flight_offers = offers

            tour = assemble_package(params, hotels, flight_offers, demo=demo)
            if demo and not flight_offers:
                demo_row = db.get_flights(
                    to_city=dest, source_site="demo", limit=1
                )
                tour = attach_db_flight(tour, demo_row[0] if demo_row else None)

            tour = mark_demo_tour(tour) if demo else tour
            db.save_tour(qid, tour, tour.get("total_price", 0))
            tour["formatted"] = format_package_html(tour, params, demo=demo)
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


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    db = get_db()
    today = db.get_today_stats()
    leads = db.get_recent_leads(30)
    tours = db.get_recent_tours(15)
    leads_today = db.count_leads_today()

    def esc(s):
        return (
            str(s or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    lead_rows = ""
    for lead in leads:
        lead_rows += f"""<tr>
          <td>{lead.get('id')}</td>
          <td>{esc(lead.get('created_at'))}</td>
          <td>{esc(lead.get('name'))}</td>
          <td>{esc(lead.get('phone'))}</td>
          <td>{esc(lead.get('tour_name'))}</td>
          <td>{esc(lead.get('message'))}</td>
        </tr>"""

    tour_rows = ""
    for t in tours:
        tour_rows += f"""<tr>
          <td>{t.get('id')}</td>
          <td>{esc(t.get('created_at'))}</td>
          <td>{esc(t.get('total_price'))} ₽</td>
          <td>{esc((t.get('user_input') or '')[:80])}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="ru"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Панель менеджера — Бон Вояж</title>
<style>
body{{font-family:Inter,system-ui,sans-serif;background:#f8fafc;color:#1e293b;margin:0;padding:24px}}
h1{{color:#01773a}} .stats{{display:flex;gap:16px;flex-wrap:wrap;margin:20px 0}}
.card{{background:#fff;border-radius:16px;padding:16px 20px;box-shadow:0 2px 8px rgba(0,0,0,.06);min-width:140px}}
.card b{{font-size:1.6rem;color:#01773a;display:block}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;margin:16px 0}}
th,td{{padding:10px 12px;border-bottom:1px solid #eef2f6;font-size:0.9rem;text-align:left}}
th{{background:#f0fdf4;color:#01773a}}
a{{color:#01773a}}
</style></head><body>
<h1>Панель менеджера</h1>
<p><a href="/">← К подбору тура</a></p>
<div class="stats">
  <div class="card"><b>{today.get('requests_count', 0)}</b>запросов сегодня</div>
  <div class="card"><b>{today.get('tours_generated', 0)}</b>собрано пакетов</div>
  <div class="card"><b>{leads_today}</b>заявок сегодня</div>
  <div class="card"><b>{len(sessions)}</b>активных сессий</div>
</div>
<h2>Заявки клиентов</h2>
<table><thead><tr><th>ID</th><th>Дата</th><th>Имя</th><th>Телефон</th><th>Тур</th><th>Сообщение</th></tr></thead>
<tbody>{lead_rows or '<tr><td colspan="6">Заявок пока нет</td></tr>'}</tbody></table>
<h2>Обучение диалога</h2>
<p id="trainingStats">Загрузка...</p>
<script>
fetch('/api/training/stats').then(r=>r.json()).then(d=>{{
  document.getElementById('trainingStats').innerHTML =
    'Примеров: <b>'+d.total_examples+'</b>, ready: <b>'+d.ready_examples+
    '</b>, точность правил: <b>'+d.validation_avg_pct+'%</b>. '+
    '<a href="/api/training/stats">JSON</a>';
}}).catch(()=>{{}});
</script>
<h2>Собранные турпакеты</h2>
<table><thead><tr><th>ID</th><th>Дата</th><th>Сумма</th><th>Запрос</th></tr></thead>
<tbody>{tour_rows or '<tr><td colspan="4">Пакетов пока нет</td></tr>'}</tbody></table>
</body></html>"""
    return HTMLResponse(html)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
