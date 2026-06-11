"""python scripts/test_dates.py"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from date_validation import validate_collected_dates

cases = [
    {"date_from": "2026-05-21", "date_to": "2026-05-20"},
    {"date_from": "2025-01-01", "date_to": "2025-01-10"},
    {"date_from": date.today().isoformat(), "date_to": "2099-01-01"},
]

for c in cases:
    ok, msg, out = validate_collected_dates(c)
    print(c, "->", ok, msg or "OK", out)
