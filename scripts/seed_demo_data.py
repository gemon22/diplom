"""Загрузка 30 тестовых записей (15 отелей + 15 перелётов) для демо-режима."""
import sys
from pathlib import Path

backend = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend))

from database import get_db  # noqa: E402
from demo_mode import DEMO_FLIGHTS, DEMO_HOTELS, seed_demo_data  # noqa: E402


def main():
    db = get_db()
    total = seed_demo_data(db)
    print(f"Готово: {total} записей (отели: {len(DEMO_HOTELS)}, перелёты: {len(DEMO_FLIGHTS)})")
    print("В чате напишите: «давай перейдем в режим демонстрации»")


if __name__ == "__main__":
    main()
