"""
Точка входа для production (Timeweb App Platform, VPS, Docker).
Запуск: uvicorn main:app --host 0.0.0.0 --port 8000
"""
import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from app import app  # noqa: E402

__all__ = ["app"]
