#!/usr/bin/env python3
"""Исправить битые ссылки /tury в таблице hotels."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from database import get_db
from tour_links import fix_stale_urls_in_db

if __name__ == "__main__":
    n = fix_stale_urls_in_db(get_db())
    print(f"Обновлено записей: {n}")
