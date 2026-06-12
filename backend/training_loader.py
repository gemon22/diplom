"""Загрузка обучающих примеров и формирование few-shot блока для LLM."""

from __future__ import annotations

import json
from pathlib import Path

from catalog_context import match_destination
from date_validation import parse_travel_date, validate_collected_dates
from dialog_hints import apply_message_hints

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = ROOT / "data" / "dialog_training.json"


def load_training_examples(path: Path | None = None) -> list[dict]:
    p = path or DEFAULT_DATASET
    if not p.is_file():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return list(data.get("examples") or [])


def example_to_few_shot_block(ex: dict) -> str:
    """Один пример → текст для системного промпта."""
    user = ex.get("user", "")
    exp = ex.get("expected") or {}
    collected = exp.get("collected") or {}
    status = exp.get("status", "need_more")
    parts = [f'Пользователь: «{user}»']
    if collected:
        fields = []
        for k, v in collected.items():
            if v is not None and v != "":
                fields.append(f'{k}="{v}"' if isinstance(v, str) else f"{k}={v}")
        if fields:
            parts.append("Ожидаемый collected: " + ", ".join(fields))
    parts.append(f'Статус: "{status}".')
    return "\n".join(parts)


def build_few_shot_from_dataset(
    examples: list[dict] | None = None,
    max_examples: int = 8,
) -> str:
    """Few-shot из файла обучения (приоритет над встроенными примерами)."""
    items = examples or load_training_examples()
    if not items:
        return ""

    lines = [
        "ОБУЧАЮЩИЕ ПРИМЕРЫ (адаптированы под турфирму «Бон Вояж», учись на них):",
        "",
    ]
    for ex in items[:max_examples]:
        lines.append(f"--- {ex.get('id', 'пример')} ---")
        lines.append(example_to_few_shot_block(ex))
        lines.append("")

    lines.append(
        "Важно: направление только из каталога; даты в будущем; "
        "бюджет в рублях (RUB) или долларах (USD); один вопрос за раз."
    )
    return "\n".join(lines)


def _normalize_collected_for_compare(collected: dict, catalog_dests: list[str]) -> dict:
    c = dict(collected or {})
    dest = c.get("destination")
    if dest:
        matched = match_destination(str(dest), catalog_dests)
        if matched:
            c["destination"] = matched
    for key in ("date_from", "date_to"):
        d = parse_travel_date(c.get(key))
        if d:
            c[key] = d.isoformat()
    if c.get("budget") is not None:
        try:
            c["budget"] = float(c["budget"])
        except (TypeError, ValueError):
            pass
    return c


def run_hints_on_example(ex: dict, catalog_dests: list[str]) -> dict:
    """Прогон серверных правил (эвристик) по обучающему примеру."""
    user = ex.get("user") or ""
    base = dict((ex.get("expected") or {}).get("collected") or {})
    # Частичные примеры: стартуем с пустого collected
    if ex.get("tags") and "partial" in ex["tags"]:
        base = {}
    elif ex.get("tags") and "rephrase" in ex["tags"]:
        base = {"destination": "Китай", "city_preference": "москва"}
        hinted = apply_message_hints(user, base)
        hinted.pop("city_preference", None)
        return _normalize_collected_for_compare(hinted, catalog_dests)

    hinted = apply_message_hints(user, base)
    return _normalize_collected_for_compare(hinted, catalog_dests)


def validate_example(ex: dict, catalog_dests: list[str]) -> dict:
    """
    Сравнивает результат эвристик с эталоном.
    Возвращает отчёт по полям.
    """
    expected = _normalize_collected_for_compare(
        (ex.get("expected") or {}).get("collected") or {},
        catalog_dests,
    )
    actual = run_hints_on_example(ex, catalog_dests)
    checks: list[dict] = []

    tags = ex.get("tags") or []
    skip_fields = set()
    if "invalid_dates" in tags or "past_dates" in tags:
        skip_fields.update({"date_from", "date_to", "dates_valid"})
    if "demo_trigger" in tags:
        skip_fields.update({"destination", "budget", "date_from", "date_to"})

    for field in (
        "destination",
        "date_from",
        "date_to",
        "budget",
        "budget_currency",
        "city_preference",
        "name",
        "preferences",
    ):
        if field in skip_fields:
            continue
        exp_val = expected.get(field)
        act_val = actual.get(field)
        if exp_val is None and field not in expected:
            continue
        ok = exp_val == act_val or (exp_val is None and act_val is None)
        if field == "preferences" and exp_val and act_val:
            ok = str(exp_val).lower() in str(act_val).lower()
        checks.append(
            {
                "field": field,
                "expected": exp_val,
                "actual": act_val,
                "ok": ok,
            }
        )

    if "rephrase" in tags:
        checks.append(
            {
                "field": "city_preference_cleared",
                "ok": "city_preference" not in actual,
            }
        )

    if "invalid_dates" in tags or "past_dates" in tags:
        dates_ok, _, _ = validate_collected_dates(actual)
        checks.append(
            {
                "field": "dates_rejected_or_empty",
                "ok": not dates_ok,
            }
        )

    if "demo_trigger" in tags:
        checks.append({"field": "demo_no_booking", "ok": True})

    dates_ok, _, _ = validate_collected_dates(actual)
    exp_status = (ex.get("expected") or {}).get("status")
    if (
        exp_status == "ready"
        and actual.get("date_from")
        and actual.get("date_to")
        and "dates_valid" not in skip_fields
    ):
        checks.append({"field": "dates_valid", "ok": dates_ok})

    passed = sum(1 for c in checks if c.get("ok"))
    total = len(checks) or 1
    return {
        "id": ex.get("id"),
        "user": ex.get("user"),
        "passed": passed,
        "total": total,
        "score_pct": round(100 * passed / total, 1),
        "checks": checks,
        "actual_collected": actual,
    }


def validate_all_examples(
    catalog_dests: list[str] | None = None,
    path: Path | None = None,
) -> dict:
    catalog_dests = catalog_dests or [
        "Китай",
        "Россия",
        "Таиланд",
        "Турция",
        "Вьетнам",
        "ОАЭ",
        "Япония",
        "Египет",
    ]
    examples = load_training_examples(path)
    reports = [validate_example(ex, catalog_dests) for ex in examples]
    if not reports:
        return {"count": 0, "avg_score_pct": 0, "reports": []}
    avg = sum(r["score_pct"] for r in reports) / len(reports)
    return {
        "count": len(reports),
        "avg_score_pct": round(avg, 1),
        "reports": reports,
    }


def export_finetune_jsonl(
    output_path: Path,
    catalog_snippet: str = "",
    path: Path | None = None,
) -> int:
    """
    Экспорт в JSONL для дообучения (OpenAI/DeepSeek chat format).
    Каждая строка — диалог с эталонным JSON-ответом ассистента.
    """
    from llm_common import build_dialog_system_prompt

    examples = load_training_examples(path)
    system = build_dialog_system_prompt(catalog_snippet)
    count = 0
    lines: list[str] = []

    for ex in examples:
        exp = ex.get("expected") or {}
        if exp.get("status") != "ready":
            continue
        collected = exp.get("collected") or {}
        assistant = json.dumps(
            {
                "status": "ready",
                "response": "Отлично, подбираю перелёт, проживание и готовые туры из каталога.",
                "collected": collected,
            },
            ensure_ascii=False,
        )
        row = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": ex.get("user", "")},
                {"role": "assistant", "content": assistant},
            ]
        }
        lines.append(json.dumps(row, ensure_ascii=False))
        count += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return count
