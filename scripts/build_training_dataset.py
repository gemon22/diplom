#!/usr/bin/env python3
"""Генерация датасета с актуальными датами (относительно сегодня)."""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "dialog_training.json"


def d(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def main() -> int:
    examples = [
        {
            "id": "bv-01",
            "user": f"Хочу в Китай с {d(40)} по {d(50)}, бюджет 80 000 руб, меня зовут Анна",
            "expected": {
                "status": "ready",
                "collected": {
                    "destination": "Китай",
                    "date_from": d(40),
                    "date_to": d(50),
                    "budget": 80000,
                    "budget_currency": "RUB",
                    "name": "Анна",
                },
            },
            "tags": ["china", "dates", "budget", "name"],
        },
        {
            "id": "bv-02",
            "user": f"Таиланд, с 5 августа на 10 дней, до 120000",
            "expected": {
                "status": "ready",
                "collected": {"destination": "Таиланд", "budget": 120000},
            },
            "tags": ["thailand", "duration", "budget"],
        },
        {
            "id": "bv-03",
            "user": "Хэйхэ выходные, бюджет 25000",
            "expected": {
                "status": "ready",
                "collected": {"destination": "Китай", "budget": 25000},
            },
            "tags": ["china", "heihe", "budget"],
        },
        {
            "id": "bv-04",
            "user": "Россия, Москва, 1–8 сентября, 60000 рублей",
            "expected": {
                "status": "ready",
                "collected": {
                    "destination": "Россия",
                    "city_preference": "москва",
                    "budget": 60000,
                },
            },
            "tags": ["russia", "moscow"],
        },
        {
            "id": "bv-05",
            "user": "с 21 мая по 20 мая",
            "expected": {"status": "need_more", "collected": {}},
            "tags": ["invalid_dates"],
        },
        {
            "id": "bv-06",
            "user": "Хочу на Мальдивы, 100000",
            "expected": {
                "status": "need_more",
                "collected": {"budget": 100000},
            },
            "tags": ["unknown_destination"],
        },
        {
            "id": "bv-07",
            "user": "Вьетнам, 15 ноября, 7 дней, бюджет 90000",
            "expected": {
                "status": "ready",
                "collected": {"destination": "Вьетнам", "budget": 90000},
            },
            "tags": ["vietnam", "duration"],
        },
        {
            "id": "bv-08",
            "user": "Турция, семейный отдых, 1 июня по 14 июня, 150000 руб",
            "expected": {
                "status": "ready",
                "collected": {
                    "destination": "Турция",
                    "budget": 150000,
                    "preferences": "семейн",
                },
            },
            "tags": ["turkey", "preferences"],
        },
        {
            "id": "bv-09",
            "user": "Китай",
            "expected": {
                "status": "need_more",
                "collected": {"destination": "Китай"},
            },
            "tags": ["partial"],
        },
        {
            "id": "bv-10",
            "user": "бюджет 50000",
            "expected": {
                "status": "need_more",
                "collected": {"budget": 50000},
            },
            "tags": ["partial", "budget"],
        },
        {
            "id": "bv-11",
            "user": "Сочи, море, 20 июля по 27 июля, 45000",
            "expected": {
                "status": "ready",
                "collected": {
                    "destination": "Россия",
                    "budget": 45000,
                },
            },
            "tags": ["russia", "sochi"],
        },
        {
            "id": "bv-12",
            "user": "Шанхай школьники, лето, бюджет 200000",
            "expected": {
                "status": "need_more",
                "collected": {
                    "destination": "Китай",
                    "budget": 200000,
                    "preferences": "школьник",
                },
            },
            "tags": ["china", "school"],
        },
        {
            "id": "bv-13",
            "user": "ОАЭ, 10–17 декабря, $3000",
            "expected": {
                "status": "ready",
                "collected": {
                    "destination": "ОАЭ",
                    "budget": 3000,
                    "budget_currency": "USD",
                },
            },
            "tags": ["uae", "usd"],
        },
        {
            "id": "bv-14",
            "user": "предложи другие варианты",
            "expected": {"status": "need_more", "collected": {}},
            "tags": ["rephrase"],
        },
        {
            "id": "bv-15",
            "user": "Из Благовещенска в Китай, 12–19 октября, 70000 руб",
            "expected": {
                "status": "ready",
                "collected": {
                    "destination": "Китай",
                    "budget": 70000,
                    "preferences": "Благовещенск",
                },
            },
            "tags": ["china", "blagoveshchensk"],
        },
        {
            "id": "bv-16",
            "user": "Бэйдайхэ летом, 10 дней, бюджет 55000",
            "expected": {
                "status": "need_more",
                "collected": {"destination": "Китай", "budget": 55000},
            },
            "tags": ["china", "beidaihe"],
        },
        {
            "id": "bv-17",
            "user": "Хэминху термальные источники, 7 дней, 48000 руб",
            "expected": {
                "status": "need_more",
                "collected": {
                    "destination": "Китай",
                    "budget": 48000,
                    "preferences": "лечебн",
                },
            },
            "tags": ["china", "heminhu"],
        },
        {
            "id": "bv-18",
            "user": "Космодром Восточный, школьная группа, 10150 на человека",
            "expected": {
                "status": "need_more",
                "collected": {
                    "destination": "Россия",
                    "budget": 10150,
                    "preferences": "школьник",
                },
            },
            "tags": ["russia", "space"],
        },
        {
            "id": "bv-19",
            "user": "Дальянь пляж, август, 71237 рублей",
            "expected": {
                "status": "need_more",
                "collected": {
                    "destination": "Китай",
                    "budget": 71237,
                    "preferences": "пляж",
                },
            },
            "tags": ["china", "dalian"],
        },
        {
            "id": "bv-20",
            "user": f"Китай, {d(30)} по {d(37)}, бюджет 65000",
            "expected": {
                "status": "ready",
                "collected": {
                    "destination": "Китай",
                    "date_from": d(30),
                    "date_to": d(37),
                    "budget": 65000,
                },
            },
            "tags": ["china", "iso_dates"],
        },
        {
            "id": "bv-21",
            "user": "Япония, 14 дней, 130000",
            "expected": {
                "status": "need_more",
                "collected": {"destination": "Япония", "budget": 130000},
            },
            "tags": ["japan"],
        },
        {
            "id": "bv-22",
            "user": "Египет, зима, 110000 руб",
            "expected": {
                "status": "need_more",
                "collected": {"destination": "Египет", "budget": 110000},
            },
            "tags": ["egypt"],
        },
        {
            "id": "bv-23",
            "user": "Пхукет, 1–10 марта, 95000",
            "expected": {
                "status": "ready",
                "collected": {"destination": "Таиланд", "budget": 95000},
            },
            "tags": ["thailand", "phuket"],
        },
        {
            "id": "bv-24",
            "user": "Нячанг, море, бюджет 60к",
            "expected": {
                "status": "need_more",
                "collected": {"destination": "Вьетнам", "budget": 60000},
            },
            "tags": ["vietnam", "budget_k"],
        },
        {
            "id": "bv-25",
            "user": "Анталия, 5–12 июля, 85000 рублей",
            "expected": {
                "status": "ready",
                "collected": {"destination": "Турция", "budget": 85000},
            },
            "tags": ["turkey", "antalya"],
        },
        {
            "id": "bv-26",
            "user": "Камчатка, дикая природа, 150000",
            "expected": {
                "status": "need_more",
                "collected": {"destination": "Россия", "budget": 150000},
            },
            "tags": ["russia", "kamchatka"],
        },
        {
            "id": "bv-27",
            "user": "давай перейдем в режим демонстрации",
            "expected": {"status": "need_more", "collected": {}},
            "tags": ["demo_trigger"],
        },
        {
            "id": "bv-28",
            "user": "Меня зовут Игорь, хочу в Таиланд",
            "expected": {
                "status": "need_more",
                "collected": {"destination": "Таиланд", "name": "Игорь"},
            },
            "tags": ["partial", "name"],
        },
        {
            "id": "bv-29",
            "user": "с 1 января 2020 по 10 января 2020",
            "expected": {"status": "need_more", "collected": {}},
            "tags": ["past_dates"],
        },
        {
            "id": "bv-30",
            "user": "Фукуок, перелёт и отель отдельно, 100000",
            "expected": {
                "status": "need_more",
                "collected": {"destination": "Вьетнам", "budget": 100000},
            },
            "tags": ["vietnam", "modular_intent"],
        },
    ]

    payload = {
        "version": 2,
        "description": "Обучающие примеры диалога ООО «Бон Вояж» (автогенерация)",
        "generated_on": date.today().isoformat(),
        "examples": examples,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: {len(examples)} примеров -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
