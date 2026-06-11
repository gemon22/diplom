"""Проверка GigaChat: python scripts/test_gigachat.py"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from config import Config
from gigachat_client import gigachat


async def main():
    print("Auth URL:", Config.GIGACHAT_AUTH_URL)
    print("Chat URL:", Config.GIGACHAT_API_URL)
    print("Model:   ", Config.GIGACHAT_MODEL)
    print("SSL verify:", Config.GIGACHAT_VERIFY_SSL)
    cred = Config.GIGACHAT_CREDENTIALS
    print("Credentials:", (cred[:12] + "...") if len(cred) > 12 else "(не задан)")

    text = await gigachat.chat(
        [{"role": "user", "content": "Ответь одним словом: ок"}]
    )
    if text:
        print("OK:", text.strip()[:200])
        return 0
    print("ОШИБКА:", gigachat.last_error)
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
