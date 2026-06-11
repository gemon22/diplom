"""Контекст каталога туров из БД для «обучения» диалога (RAG / few-shot)."""
from __future__ import annotations

from typing import Any


def _normalize_dest(s: str) -> str:
    return (s or "").strip().lower()


def match_destination(user_input: str, available: list[str]) -> str | None:
    """Сопоставляет ввод пользователя с направлением из каталога."""
    if not user_input or not available:
        return None
    u = _normalize_dest(user_input)
    aliases = {
        "китай": "Китай",
        "china": "Китай",
        "хэйхэ": "Китай",
        "шанхай": "Китай",
        "россия": "Россия",
        "рф": "Россия",
        "москва": "Россия",
        "моск": "Россия",
        "тайланд": "Таиланд",
        "таиланд": "Таиланд",
        "турция": "Турция",
        "вьетнам": "Вьетнам",
    }
    for key, canonical in aliases.items():
        if key in u and canonical in available:
            return canonical
    for d in available:
        if _normalize_dest(d) in u or u in _normalize_dest(d):
            return d
    return None


def build_catalog_snippet(rows: list[dict], max_tours: int = 12) -> str:
    """
    rows: список туров из БД (name, destination, total_stay_price).
    """
    if not rows:
        return (
            "КАТАЛОГ: пуст. Предложи пользователю оставить заявку менеджеру. "
            "Направления пока не загружены (нужен запуск парсера)."
        )

    by_dest: dict[str, list[dict]] = {}
    for r in rows:
        dest = r.get("destination") or "Неизвестно"
        by_dest.setdefault(dest, []).append(r)

    lines = [
        "КАТАЛОГ ТУРФИРМЫ (реальные предложения с сайта, цены в РУБЛЯХ за пакет):",
        "Предлагай ТОЛЬКО направления из списка ниже. Если пользователь просит другую страну — "
        "вежливо скажи, что в каталоге есть варианты:",
    ]
    destinations = sorted(by_dest.keys())
    lines.append("Направления: " + ", ".join(destinations))

    shown = 0
    for dest in destinations:
        tours = sorted(
            by_dest[dest],
            key=lambda x: float(x.get("total_stay_price") or 0),
        )
        for t in tours[:3]:
            if shown >= max_tours:
                break
            price = int(float(t.get("total_stay_price") or 0))
            name = (t.get("name") or "")[:80]
            lines.append(f"  • [{dest}] {name} — от {price} ₽")
            shown += 1
        if shown >= max_tours:
            break

    prices = [
        int(float(r.get("total_stay_price") or 0))
        for r in rows
        if float(r.get("total_stay_price") or 0) > 0
    ]
    if prices:
        lines.append(f"Диапазон цен в каталоге: от {min(prices)} до {max(prices)} ₽.")

    return "\n".join(lines)


def normalize_collected_destination(collected: dict, catalog_rows: list[dict]) -> dict:
    """Подставляет каноническое название направления из каталога."""
    collected = dict(collected)
    dest = collected.get("destination")
    if not dest:
        return collected
    available = list({r.get("destination") for r in catalog_rows if r.get("destination")})
    matched = match_destination(str(dest), available)
    if matched:
        collected["destination"] = matched
    return collected
