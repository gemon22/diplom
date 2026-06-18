"""Генерация схемы БД в формате для диплома."""
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).resolve().parent / "db_schema.png"

TABLES = [
    {
        "num": 1,
        "name": "hotels",
        "desc": "Каталог туров/отелей",
        "fields": [
            ("id", "INT PK"),
            ("name", "VARCHAR(255)"),
            ("destination", "VARCHAR(100)"),
            ("price_per_night", "DECIMAL(10,2)"),
            ("total_stay_price", "DECIMAL(10,2)"),
            ("amenities", "TEXT"),
            ("rating", "FLOAT"),
            ("source_url", "VARCHAR(512)"),
            ("source_site", "VARCHAR(255)"),
            ("last_updated", "TIMESTAMP"),
        ],
    },
    {
        "num": 2,
        "name": "flights",
        "desc": "Авиапредложения",
        "fields": [
            ("id", "INT PK"),
            ("from_city", "VARCHAR(100)"),
            ("to_city", "VARCHAR(100)"),
            ("departure_date", "DATE"),
            ("return_date", "DATE"),
            ("price", "DECIMAL(10,2)"),
            ("airline", "VARCHAR(100)"),
            ("source_site", "VARCHAR(255)"),
            ("last_updated", "TIMESTAMP"),
        ],
    },
    {
        "num": 3,
        "name": "user_sessions",
        "desc": "Сессии диалога",
        "fields": [
            ("session_id", "VARCHAR(100) PK"),
            ("dialog_state", "JSON"),
            ("created_at", "TIMESTAMP"),
            ("updated_at", "TIMESTAMP"),
        ],
    },
    {
        "num": 4,
        "name": "user_queries",
        "desc": "Сообщения пользователя",
        "fields": [
            ("id", "INT PK"),
            ("session_id", "VARCHAR(100) FK"),
            ("user_input", "TEXT"),
            ("extracted_params", "JSON"),
            ("created_at", "TIMESTAMP"),
        ],
    },
    {
        "num": 5,
        "name": "generated_tours",
        "desc": "Собранные турпакеты",
        "fields": [
            ("id", "INT PK"),
            ("query_id", "INT FK"),
            ("tour_package", "JSON"),
            ("total_price", "DECIMAL(10,2)"),
            ("created_at", "TIMESTAMP"),
        ],
    },
    {
        "num": 6,
        "name": "daily_stats",
        "desc": "Статистика",
        "fields": [
            ("date", "DATE PK"),
            ("requests_count", "INT"),
            ("tours_generated", "INT"),
            ("avg_response_time_ms", "INT"),
        ],
    },
    {
        "num": 7,
        "name": "agency_leads",
        "desc": "Заявки клиентов",
        "fields": [
            ("id", "INT PK"),
            ("session_id", "VARCHAR(100)"),
            ("name", "VARCHAR(255)"),
            ("phone", "VARCHAR(50)"),
            ("email", "VARCHAR(255)"),
            ("message", "TEXT"),
            ("tour_name", "VARCHAR(512)"),
            ("created_at", "TIMESTAMP"),
        ],
    },
]

HEADER = "#1a365d"
HEADER_TEXT = "white"
BODY_BG = "#ffffff"
BORDER = "#1a365d"
FIELD = "#1e293b"
TYPE_CLR = "#475569"


def draw_table(ax, cx, cy, w, table, row_h=0.22, header_h=0.55):
    fields = table["fields"]
    body_h = len(fields) * row_h + 0.12
    h = header_h + body_h
    x, y = cx - w / 2, cy - h / 2

    outer = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="square,pad=0",
        linewidth=1.4,
        edgecolor=BORDER,
        facecolor=BODY_BG,
        zorder=3,
    )
    ax.add_patch(outer)

    header = mpatches.Rectangle(
        (x, y + h - header_h), w, header_h, facecolor=HEADER, edgecolor=BORDER, linewidth=1.4, zorder=4
    )
    ax.add_patch(header)

    title = f"Таблица {table['num']} — {table['name']}"
    ax.text(cx, y + h - header_h * 0.62, title, ha="center", va="center", fontsize=8.2, fontweight="bold", color=HEADER_TEXT, zorder=5)
    ax.text(cx, y + h - header_h * 0.28, table["desc"], ha="center", va="center", fontsize=7.2, color="#dbeafe", zorder=5)

    fy = y + h - header_h - 0.08
    for fname, ftype in fields:
        fy -= row_h
        ax.text(x + 0.1, fy + row_h * 0.5, fname, ha="left", va="center", fontsize=6.8, color=FIELD, zorder=5)
        ax.text(x + w - 0.1, fy + row_h * 0.5, ftype, ha="right", va="center", fontsize=6.5, color=TYPE_CLR, zorder=5)

    return {"x": x, "y": y, "w": w, "h": h, "cx": cx, "cy": cy, "top": y + h, "bottom": y, "left": x, "right": x + w}


def connect(ax, p1, p2, dashed=False, label1=None, label2=None):
    style = "dashed" if dashed else "solid"
    ls = (0, (5, 3)) if dashed else "solid"
    arr = FancyArrowPatch(
        p1,
        p2,
        arrowstyle="-",
        linestyle=ls,
        linewidth=1.2,
        color="#334155",
        mutation_scale=1,
        zorder=2,
    )
    ax.add_patch(arr)
    if label1:
        ax.text(p1[0], p1[1], label1, fontsize=8, fontweight="bold", color="#0f172a", ha="center", va="bottom", zorder=6)
    if label2:
        ax.text(p2[0], p2[1], label2, fontsize=8, fontweight="bold", color="#0f172a", ha="center", va="top", zorder=6)


def main():
    fig, ax = plt.subplots(figsize=(18, 12))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 12)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(
        9,
        11.45,
        "Схема базы данных MySQL — система подбора туров",
        ha="center",
        va="center",
        fontsize=15,
        fontweight="bold",
        color="#0f172a",
    )

    # Позиции как на образце
    pos = {
        1: (3.0, 9.2, 3.6),   # hotels
        2: (9.0, 9.2, 3.6),   # flights
        6: (15.0, 9.2, 3.4),  # daily_stats
        3: (4.2, 5.9, 3.5),   # user_sessions
        4: (9.0, 5.9, 3.6),   # user_queries
        7: (14.2, 5.9, 3.6),  # agency_leads
        5: (9.0, 2.3, 3.6),   # generated_tours
    }

    boxes = {}
    for t in TABLES:
        cx, cy, w = pos[t["num"]]
        boxes[t["num"]] = draw_table(ax, cx, cy, w, t)

    # Примечания к независимым таблицам
    ax.text(3.0, 7.35, "заполняется парсером", ha="center", fontsize=6.5, color="#64748b", style="italic")
    ax.text(9.0, 7.35, "заполняется API", ha="center", fontsize=6.5, color="#64748b", style="italic")

    s3, q4, g5, l7 = boxes[3], boxes[4], boxes[5], boxes[7]

    # user_sessions 1 — N user_queries (логическая, пунктир)
    connect(ax, (s3["right"], s3["cy"]), (q4["left"], q4["cy"]), dashed=True, label1="1", label2="N")

    # user_queries 1 — N generated_tours (физическая FK)
    connect(ax, (q4["cx"], q4["bottom"]), (g5["cx"], g5["top"]), dashed=False, label1="1", label2="N")

    # user_sessions 1 — N agency_leads (логическая, пунктир)
    connect(
        ax,
        (s3["cx"] + 0.5, s3["top"] - 0.1),
        (l7["left"], l7["cy"] + 0.3),
        dashed=True,
        label1="1",
        label2="N",
    )

    plt.savefig(OUT, dpi=220, bbox_inches="tight", facecolor="white", pad_inches=0.25)
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
