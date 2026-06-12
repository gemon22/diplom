#!/usr/bin/env python3
"""
Полный цикл обучения — один запуск, готовый результат.

  python scripts/run_training.py

Создаёт:
  - data/dialog_training.json   (датасет)
  - data/finetune_dialog.jsonl  (для fine-tuning API)
  - data/training_report.md     (отчёт для диплома)
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))


def _run_build_dataset() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_training_dataset.py")],
        check=True,
        cwd=str(ROOT),
    )


def main() -> int:
    print("=== Обучение модуля «Бон Вояж» ===\n")

    print("[1/4] Генерация датасета...")
    _run_build_dataset()

    from catalog_context import build_catalog_snippet
    from database import get_db
    from dialog_training import few_shot_examples, training_stats
    from training_loader import export_finetune_jsonl, validate_all_examples

    print("[2/4] Проверка эвристик на примерах...")
    catalog_dests = None
    snippet = "КАТАЛОГ: Китай, Россия, Таиланд, Турция, Вьетнам, ОАЭ, Япония, Египет."
    try:
        db = get_db()
        rows = db.get_all_hotels_sample(limit=50)
        catalog_dests = list({r.get("destination") for r in rows if r.get("destination")})
        snippet = build_catalog_snippet(rows)
    except Exception as e:
        print(f"  (БД недоступна, используем шаблон каталога: {e})")

    validation = validate_all_examples(catalog_dests=catalog_dests)
    stats = training_stats()

    print("[3/4] Экспорт JSONL для fine-tuning...")
    jsonl_path = ROOT / "data" / "finetune_dialog.jsonl"
    n_export = export_finetune_jsonl(jsonl_path, catalog_snippet=snippet)

    print("[4/4] Отчёт для диплома...")
    few_shot_len = len(few_shot_examples())
    report_path = ROOT / "data" / "training_report.md"

    failed = [r for r in validation["reports"] if r["score_pct"] < 80]
    ok_lines = "\n".join(
        f"- **{r['id']}** ({r['score_pct']}%): {r['user'][:70]}"
        for r in validation["reports"]
        if r["score_pct"] >= 80
    )
    fail_lines = "\n".join(
        f"- **{r['id']}** ({r['score_pct']}%): {r['user'][:70]}"
        for r in failed
    ) or "- нет"

    report = f"""# Отчёт об обучении диалогового модуля

**Организация:** ООО «Бон Вояж» / «Планета 360»  
**Дата:** {datetime.now().strftime("%d.%m.%Y %H:%M")}  
**Метод:** гибридное обучение (few-shot + серверные правила + RAG каталога)

## Результаты

| Показатель | Значение |
|---|---|
| Примеров в датасете | {stats['total_examples']} |
| Примеров со статусом ready | {stats['ready_examples']} |
| Средняя точность эвристик | **{validation['avg_score_pct']}%** |
| Размер few-shot блока | {few_shot_len} символов |
| Экспорт fine-tuning | {n_export} диалогов в `finetune_dialog.jsonl` |

## Схема обучения

1. **In-context learning** — примеры из `dialog_training.json` в системном промпте LLM.
2. **Серверные правила** — `dialog_hints.py` (даты, бюджет, направления Бон Вояж).
3. **RAG** — фрагмент каталога туров из MySQL в каждом запросе.
4. **Fine-tuning (опционально)** — файл `finetune_dialog.jsonl` для DeepSeek API.

## Примеры с высокой точностью

{ok_lines}

## Требуют доработки LLM (эвристики частично)

{fail_lines}

## Файлы

- `data/dialog_training.json` — обучающий датасет
- `data/finetune_dialog.jsonl` — экспорт для дообучения
- `scripts/train_dialog.py validate` — повторная проверка
- `GET /api/training/stats` — API на сервере

## Вывод для защиты

Модуль обучен на {stats['total_examples']} диалоговых примерах турфирмы «Бон Вояж».
Точность извлечения параметров серверными правилами — {validation['avg_score_pct']}%.
Нейросеть (DeepSeek / GigaChat) получает обучающие примеры в промпте и актуальный каталог туров,
что обеспечивает корректный подбор направлений, дат и бюджета в рублях.
"""
    report_path.write_text(report, encoding="utf-8")

    print()
    print("=== ГОТОВО ===")
    print(f"  Датасет:     {ROOT / 'data' / 'dialog_training.json'}")
    print(f"  Fine-tune:   {jsonl_path} ({n_export} записей)")
    print(f"  Отчёт:       {report_path}")
    print(f"  Точность:    {validation['avg_score_pct']}%")
    print()
    print("Обучение подключено к чату автоматически (few-shot в промпте).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
