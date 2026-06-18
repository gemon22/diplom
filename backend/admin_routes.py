"""Маршруты панели менеджера с авторизацией."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from admin_auth import (
    COOKIE_NAME,
    SESSION_MAX_AGE,
    create_session_token,
    hash_password,
    parse_session_token,
    verify_password,
)
from database import get_db

router = APIRouter(tags=["admin"])

ADMIN_HTML = Path(__file__).resolve().parent.parent / "frontend" / "admin.html"


def _esc(s) -> str:
    return (
        str(s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _current_manager(request: Request) -> dict | None:
    token = request.cookies.get(COOKIE_NAME)
    session = parse_session_token(token)
    if not session:
        return None
    return get_db().get_manager_by_id(session["id"])


def _require_manager(request: Request) -> dict:
    mgr = _current_manager(request)
    if not mgr:
        raise HTTPException(status_code=401, detail="Требуется вход")
    return mgr


def _set_session_cookie(response: Response, manager_id: int, username: str):
    response.set_cookie(
        COOKIE_NAME,
        create_session_token(manager_id, username),
        httponly=True,
        max_age=SESSION_MAX_AGE,
        samesite="lax",
    )


class LoginReq(BaseModel):
    username: str
    password: str


class ProfileReq(BaseModel):
    username: Optional[str] = None
    current_password: str
    new_password: Optional[str] = None


class NewManagerReq(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=4, max_length=128)
    role: str = "manager"


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    if not _current_manager(request):
        return HTMLResponse(_login_html())
    if ADMIN_HTML.is_file():
        return HTMLResponse(ADMIN_HTML.read_text(encoding="utf-8"))
    return HTMLResponse("<p>admin.html not found</p>")


@router.post("/admin/login")
async def admin_login(req: LoginReq, response: Response):
    db = get_db()
    mgr = db.get_manager_by_username(req.username.strip())
    if not mgr or not verify_password(req.password, mgr["password_hash"]):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    _set_session_cookie(response, mgr["id"], mgr["username"])
    return {"ok": True, "username": mgr["username"], "role": mgr["role"]}


@router.post("/admin/logout")
async def admin_logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/admin/api/me")
async def admin_me(request: Request):
    mgr = _require_manager(request)
    return {
        "id": mgr["id"],
        "username": mgr["username"],
        "role": mgr["role"],
    }


@router.get("/admin/api/dashboard")
async def admin_dashboard(request: Request):
    _require_manager(request)
    db = get_db()
    today = db.get_today_stats()
    return {
        "today_requests": today.get("requests_count", 0),
        "today_tours": today.get("tours_generated", 0),
        "leads_today": db.count_leads_today(),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/admin/api/leads")
async def admin_leads(request: Request, limit: int = 50):
    _require_manager(request)
    return get_db().get_recent_leads(limit)


@router.get("/admin/api/queries")
async def admin_queries(request: Request, limit: int = 100, since_id: int = 0):
    _require_manager(request)
    return get_db().get_recent_queries(limit=limit, since_id=since_id)


@router.get("/admin/api/tours")
async def admin_tours(request: Request, limit: int = 30):
    _require_manager(request)
    return get_db().get_recent_tours(limit)


@router.get("/admin/api/managers")
async def admin_list_managers(request: Request):
    mgr = _require_manager(request)
    if mgr["role"] != "admin":
        raise HTTPException(status_code=403, detail="Только для администратора")
    return get_db().list_managers()


@router.post("/admin/api/managers")
async def admin_create_manager(req: NewManagerReq, request: Request):
    mgr = _require_manager(request)
    if mgr["role"] != "admin":
        raise HTTPException(status_code=403, detail="Только для администратора")
    db = get_db()
    if db.get_manager_by_username(req.username.strip()):
        raise HTTPException(status_code=400, detail="Логин уже занят")
    role = req.role if req.role in ("admin", "manager") else "manager"
    mid = db.create_manager(req.username.strip(), hash_password(req.password), role)
    return {"ok": True, "id": mid}


@router.post("/admin/api/profile")
async def admin_update_profile(req: ProfileReq, request: Request):
    mgr = _require_manager(request)
    db = get_db()
    full = db.get_manager_by_username(mgr["username"])
    if not full or not verify_password(req.current_password, full["password_hash"]):
        raise HTTPException(status_code=400, detail="Неверный текущий пароль")

    new_username = (req.username or mgr["username"]).strip()
    if new_username != mgr["username"]:
        if db.get_manager_by_username(new_username):
            raise HTTPException(status_code=400, detail="Логин уже занят")

    pwd_hash = None
    if req.new_password:
        if len(req.new_password) < 4:
            raise HTTPException(status_code=400, detail="Пароль слишком короткий")
        pwd_hash = hash_password(req.new_password)

    db.update_manager_credentials(mgr["id"], new_username, pwd_hash)

    response = JSONResponse({"ok": True, "username": new_username})
    _set_session_cookie(response, mgr["id"], new_username)
    return response


@router.get("/admin/stats")
async def admin_stats_legacy(request: Request):
    _require_manager(request)
    db = get_db()
    today = db.get_today_stats()
    return {
        "today_requests": today["requests_count"],
        "today_tours": today["tours_generated"],
        "timestamp": datetime.now().isoformat(),
    }


def _login_html() -> str:
    return """<!DOCTYPE html>
<html lang="ru"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Вход — Панель менеджера</title>
<style>
*{box-sizing:border-box}body{font-family:Inter,system-ui,sans-serif;background:#f0fdf4;margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center}
.card{background:#fff;padding:32px;border-radius:20px;box-shadow:0 8px 30px rgba(0,0,0,.08);width:100%;max-width:380px}
h1{color:#01773a;font-size:1.4rem;margin:0 0 8px}p{color:#64748b;font-size:.9rem;margin:0 0 24px}
label{display:block;font-size:.85rem;color:#475569;margin-bottom:6px}
input{width:100%;padding:12px 14px;border:1px solid #e2e8f0;border-radius:12px;font-size:1rem;margin-bottom:16px}
button{width:100%;padding:12px;background:#01773a;color:#fff;border:none;border-radius:12px;font-weight:600;font-size:1rem;cursor:pointer}
button:hover{background:#02612f}.err{color:#b91c1c;font-size:.85rem;margin-top:12px;display:none}
a{color:#01773a}
</style></head><body>
<div class="card">
  <h1>Панель менеджера</h1>
  <p>ООО «Бон Вояж» — вход для сотрудников</p>
  <form id="loginForm">
    <label>Логин</label>
    <input name="username" id="username" required autocomplete="username">
    <label>Пароль</label>
    <input name="password" id="password" type="password" required autocomplete="current-password">
    <button type="submit">Войти</button>
    <p class="err" id="err"></p>
  </form>
  <p style="margin-top:20px;font-size:.85rem"><a href="/">← На сайт</a></p>
</div>
<script>
document.getElementById('loginForm').onsubmit=async function(e){
  e.preventDefault();
  const err=document.getElementById('err');
  err.style.display='none';
  const body={username:document.getElementById('username').value,password:document.getElementById('password').value};
  try{
    const r=await fetch('/admin/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    if(!r.ok){const d=await r.json().catch(()=>({}));throw new Error(d.detail||'Ошибка входа');}
    location.reload();
  }catch(x){err.textContent=x.message;err.style.display='block';}
};
</script></body></html>"""
