#!/usr/bin/env python3
"""Заполнить таблицу flights случайными перелётами."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from database import get_db
from flight_seed import FLIGHT_SOURCE, seed_catalog_flights


def main() -> int:
    force = "--force" in sys.argv
    db = get_db()
    n = seed_catalog_flights(db, force=force)
    total = db.count_flights_by_source(FLIGHT_SOURCE)
    print(f"Готово: {n} перелётов (source={FLIGHT_SOURCE}), всего в каталоге: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
