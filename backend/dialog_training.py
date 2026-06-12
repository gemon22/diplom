"""Few-shot примеры диалога (обучение модели на примерах «Бон Вояж»)."""

from date_validation import today_iso
from training_loader import build_few_shot_from_dataset, load_training_examples


def _builtin_examples() -> str:
    today = today_iso()
    return f"""
ПРИМЕРЫ ПРАВИЛЬНОГО ПОВЕДЕНИЯ (учись на них):

--- Пример 1: сбор данных ---
Пользователь: «Хочу в Китай с 10 июля по 20 июля, бюджет 80 000 руб, меня зовут Анна»
Ответ JSON: status "ready", destination "Китай", date_from "2026-07-10", date_to "2026-07-20",
budget 80000, budget_currency "RUB", name "Анна".

--- Пример 2: неверные даты (конец раньше начала) ---
Пользователь: «с 21 мая по 20 мая»
Ответ: status "need_more", response объясняет что дата окончания раньше начала, просит исправить.
date_from и date_to не ставить ready.

--- Пример 3: даты в прошлом ---
Сегодня {today}. Пользователь: «с 1 января 2024 по 10 января 2024»
Ответ: status "need_more", вежливо сказать что даты прошли, попросить будущие даты.

--- Пример 4: направления нет в каталоге ---
Каталог содержит только Китай и Россия. Пользователь: «хочу на Мальдивы»
Ответ: status "need_more", предложить Китай или Россию из каталога, не выдумывать туры.

--- Пример 5: один вопрос за раз ---
Не хватает только бюджета — спроси только про бюджет, не переспрашивай направление и даты.

--- Пример 6: сборка по отдельности ---
После ready система подберёт перелёт и проживание отдельно, плюс готовые туры из каталога.
Не обещай один «готовый пакет» — объясни, что будут оба варианта.
"""


def few_shot_examples() -> str:
    """Примеры из data/dialog_training.json + встроенные правила."""
    dataset_block = build_few_shot_from_dataset(max_examples=18)
    if dataset_block:
        return dataset_block + "\n\n" + _builtin_examples()
    return _builtin_examples()


def training_stats() -> dict:
    examples = load_training_examples()
    ready = sum(
        1 for e in examples if (e.get("expected") or {}).get("status") == "ready"
    )
    return {
        "total_examples": len(examples),
        "ready_examples": ready,
        "dataset_path": "data/dialog_training.json",
    }
