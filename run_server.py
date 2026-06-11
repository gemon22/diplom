"""Запуск API: python run_server.py"""
import sys
from pathlib import Path

backend = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
