#!/usr/bin/env python3
"""
Обучение / проверка диалогового модуля для «Бон Вояж».

Использование:
  python scripts/train_dialog.py validate   — проверка эвристик на обучающих примерах
  python scripts/train_dialog.py export     — JSONL для дообучения LLM (DeepSeek/OpenAI format)
  python scripts/train_dialog.py stats      — статистика датасета

Для диплома: гибридная схема «обучения» —
  1) few-shot примеры в системном промпте (in-context learning);
  2) серверные правила dialog_hints.py;
  3) опционально fine-tuning по экспортированному JSONL.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from catalog_context import build_catalog_snippet  # noqa: E402
from database import get_db  # noqa: E402
from dialog_training import training_stats  # noqa: E402
from training_loader import (  # noqa: E402
    export_finetune_jsonl,
    validate_all_examples,
)


def cmd_validate() -> int:
    try:
        db = get_db()
        rows = db.get_all_hotels_sample(limit=50)
        catalog_dests = list(
            {r.get("destination") for r in rows if r.get("destination")}
        )
    except Exception:
        catalog_dests = None

    report = validate_all_examples(catalog_dests=catalog_dests)
    print(f"Проверено примеров: {report['count']}")
    print(f"Средняя точность эвристик: {report['avg_score_pct']}%")
    print()

    for r in report["reports"]:
        status = "OK" if r["score_pct"] >= 80 else "!!"
        print(f"[{status}] {r['id']}: {r['score_pct']}% — {r['user'][:60]}")
        for c in r["checks"]:
            if not c.get("ok"):
                print(
                    f"      {c['field']}: ожидалось {c.get('expected')!r}, "
                    f"получено {c.get('actual')!r}"
                )
    return 0


def cmd_export() -> int:
    out = ROOT / "data" / "finetune_dialog.jsonl"
    snippet = ""
    try:
        db = get_db()
        snippet = build_catalog_snippet(db.get_all_hotels_sample(limit=30))
    except Exception:
        snippet = "КАТАЛОГ: Китай, Россия, Таиланд."

    n = export_finetune_jsonl(out, catalog_snippet=snippet)
    print(f"Экспортировано {n} диалогов -> {out}")
    print("Файл можно использовать для fine-tuning DeepSeek / OpenAI API.")
    return 0


def cmd_stats() -> int:
    s = training_stats()
    print("Датасет обучения диалога:")
    for k, v in s.items():
        print(f"  {k}: {v}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Обучение диалога «Бон Вояж»")
    parser.add_argument(
        "command",
        choices=("validate", "export", "stats"),
        help="validate | export | stats",
    )
    args = parser.parse_args()
    if args.command == "validate":
        return cmd_validate()
    if args.command == "export":
        return cmd_export()
    return cmd_stats()


if __name__ == "__main__":
    raise SystemExit(main())
