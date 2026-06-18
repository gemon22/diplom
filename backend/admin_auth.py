"""Авторизация менеджеров панели администратора."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from typing import Any

from config import Config

SESSION_MAX_AGE = 60 * 60 * 24  # 24 часа
COOKIE_NAME = "mgr_session"


def _secret() -> bytes:
    key = (Config.ADMIN_SECRET_KEY or "change-me-in-production").encode()
    return key


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000
    ).hex()
    return hmac.compare_digest(check, digest)


def create_session_token(manager_id: int, username: str) -> str:
    exp = int(time.time()) + SESSION_MAX_AGE
    payload = f"{manager_id}:{username}:{exp}"
    sig = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    raw = f"{payload}:{sig}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def parse_session_token(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        manager_id, username, exp, sig = raw.rsplit(":", 3)
        payload = f"{manager_id}:{username}:{exp}"
        expected = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if int(exp) < time.time():
            return None
        return {"id": int(manager_id), "username": username}
    except Exception:
        return None
