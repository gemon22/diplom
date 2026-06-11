"""Проверка ключа DeepSeek: python scripts/test_deepseek.py"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from config import Config
from deepseek_client import deepseek


async def main():
    print("API URL:", Config.DEEPSEEK_API_URL)
    print("Model:  ", Config.DEEPSEEK_MODEL)
    key = Config.DEEPSEEK_API_KEY
    print("Key:    ", (key[:8] + "..." + key[-4:]) if len(key) > 12 else "(не задан)")

    text = await deepseek.chat(
        [{"role": "user", "content": "Ответь одним словом: ок"}]
    )
    if text:
        print("OK, ответ API:", text.strip()[:200])
        return 0
    print("ОШИБКА:", deepseek.last_error)
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
