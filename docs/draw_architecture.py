"""Архитектурная схема модуля — PNG для презентации."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "architecture.png"

GREEN = (1, 119, 58)
GREEN2 = (2, 138, 70)
TEAL = (13, 148, 136)
DARK = (30, 41, 59)
GRAY = (100, 116, 139)
ZONE = (255, 251, 235)
BORDER = (187, 247, 208)
WHITE = (255, 255, 255)
BLUE = (219, 234, 254)
BLUE_BD = (59, 130, 246)
ARROW = (51, 65, 85)

W, H = 3200, 2240
CX = W // 2  # 1600

# Сетка: боковые колонки одинаковой ширины, центр — общая ось
MARGIN = 80
SIDE_W = 540
CENTER_L = MARGIN + SIDE_W + 40          # 660
CENTER_R = W - MARGIN - SIDE_W - 40      # 2540
CENTER_W = CENTER_R - CENTER_L           # 1880
SIDE_L = (MARGIN, MARGIN + SIDE_W)       # 80..620
SIDE_R = (W - MARGIN - SIDE_W, W - MARGIN)  # 2580..3120


def _font(size: int, bold: bool = False):
    paths = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _center_text(draw, xy, text, font, fill=DARK, anchor="mm"):
    draw.text(xy, text, font=font, fill=fill, anchor=anchor)


def _rounded_rect(draw, box, radius=18, fill=WHITE, outline=GREEN, width=3):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _zone(draw, box, title: str):
    _rounded_rect(draw, box, radius=24, fill=ZONE, outline=GREEN, width=4)
    x0, y0, x1, y1 = box
    hdr_h = 68
    draw.rectangle((x0 + 4, y0 + 4, x1 - 4, y0 + hdr_h), fill=GREEN)
    _center_text(draw, ((x0 + x1) // 2, y0 + hdr_h // 2 + 2), title, _font(32, True), WHITE)


def _box(draw, box, title: str, lines: list[str], header=GREEN, fill=WHITE):
    _rounded_rect(draw, box, radius=16, fill=fill, outline=header, width=3)
    x0, y0, x1, y1 = box
    hdr_h = 54
    draw.rectangle((x0 + 2, y0 + 2, x1 - 2, y0 + hdr_h), fill=header)
    _center_text(draw, ((x0 + x1) // 2, y0 + hdr_h // 2), title, _font(26, True), WHITE)
    if not lines:
        return
    fy = y0 + hdr_h + 28
    for line in lines:
        _center_text(draw, ((x0 + x1) // 2, fy), line, _font(23), GRAY if line.startswith("·") else DARK)
        fy += 34


def _small_table(draw, box, name: str, font_size: int = 19):
    _rounded_rect(draw, box, radius=10, fill=BLUE, outline=BLUE_BD, width=2)
    _center_text(draw, ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2), name, _font(font_size, True), DARK)


def _table_row(draw, names: list[str], y: int, tw: int, th: int, gap: int) -> list[int]:
    row_w = len(names) * tw + (len(names) - 1) * gap
    tx = CX - row_w // 2
    centers = []
    for i, name in enumerate(names):
        x = tx + i * (tw + gap)
        fs = 17 if len(name) > 14 else 19
        _small_table(draw, (x, y, x + tw, y + th), name, fs)
        centers.append(x + tw // 2)
    return centers


def _cylinder(draw, cx, cy, w, h, label: str):
    rx = w // 2
    top, bot = cy - h // 2, cy + h // 2
    body = (cx - rx, top + 18, cx + rx, bot - 18)
    draw.ellipse((cx - rx, top, cx + rx, top + 36), fill=(226, 232, 240), outline=GRAY, width=2)
    draw.rectangle(body, fill=(226, 232, 240))
    draw.ellipse((cx - rx, bot - 36, cx + rx, bot), fill=(203, 213, 225), outline=GRAY, width=2)
    draw.line((cx - rx, top + 18, cx - rx, bot - 18), fill=GRAY, width=2)
    draw.line((cx + rx, top + 18, cx + rx, bot - 18), fill=GRAY, width=2)
    _center_text(draw, (cx, cy), label, _font(28, True), DARK)


def _line_arrow(draw, points: list[tuple[int, int]], label: str | None = None, double: bool = False):
    for i in range(len(points) - 1):
        draw.line((*points[i], *points[i + 1]), fill=ARROW, width=4)
    p1, p2 = points[-2], points[-1]
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    size = 14
    draw.polygon([
        p2,
        (p2[0] - size * math.cos(ang - 0.45), p2[1] - size * math.sin(ang - 0.45)),
        (p2[0] - size * math.cos(ang + 0.45), p2[1] - size * math.sin(ang + 0.45)),
    ], fill=ARROW)
    if double:
        p0, p1b = points[0], points[1]
        ang2 = math.atan2(p0[1] - p1b[1], p0[0] - p1b[0])
        draw.polygon([
            p0,
            (p0[0] - size * math.cos(ang2 - 0.45), p0[1] - size * math.sin(ang2 - 0.45)),
            (p0[0] - size * math.cos(ang2 + 0.45), p0[1] - size * math.sin(ang2 + 0.45)),
        ], fill=ARROW)
    if label:
        mx = sum(p[0] for p in points) // len(points)
        my = sum(p[1] for p in points) // len(points)
        tw, th = _text_size(draw, label, _font(20, True))
        pad = 8
        draw.rounded_rectangle(
            (mx - tw // 2 - pad, my - th // 2 - pad, mx + tw // 2 + pad, my + th // 2 + pad),
            radius=8, fill=WHITE, outline=BORDER, width=2,
        )
        _center_text(draw, (mx, my), label, _font(20, True), GREEN)


def _hbox(xc: int, y: int, w: int, h: int) -> tuple[int, int, int, int]:
    return (xc - w // 2, y, xc + w // 2, y + h)


def main():
    img = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    _center_text(draw, (CX, 62), "Архитектурная схема модуля «AI Тур-Генератор»", _font(42, True), GREEN)
    draw.line((MARGIN, 98, W - MARGIN, 98), fill=BORDER, width=3)

    # --- Зоны (выровнены по одной ширине центра) ---
    y_client, h_client = 118, 370
    y_server, h_server = 510, 300
    y_db, h_db = 830, 640

    client_zone = (CENTER_L, y_client, CENTER_R, y_client + h_client)
    server_zone = (CENTER_L, y_server, CENTER_R, y_server + h_server)
    db_zone = (CENTER_L, y_db, CENTER_R, y_db + h_db)
    parser_zone = (SIDE_L[0], y_server, SIDE_L[1], y_db + h_db)
    ext_zone = (SIDE_R[0], y_server, SIDE_R[1], y_server + h_server)

    _zone(draw, client_zone, "Клиентская часть")
    _zone(draw, server_zone, "Серверная часть")
    _zone(draw, db_zone, "База данных MySQL")
    _zone(draw, parser_zone, "Парсер Python — раз в 12 ч")
    _zone(draw, ext_zone, "Внешние сервисы")

    # --- Блоки внутри зон ---
    cy_client = y_client + h_client // 2 + 20
    user_box = _hbox(CX - 420, cy_client, 300, 110)
    frontend_box = _hbox(CX + 280, cy_client, 920, 170)
    _box(draw, user_box, "Пользователь", [])
    _box(draw, frontend_box, "Frontend — Vue.js",
         ["bonvoyage28.ru", "· чат  ·  история  ·  карточка тура"], header=TEAL)

    cy_server = y_server + h_server // 2 + 18
    backend_box = (CENTER_L + 40, cy_server - 85, CENTER_R - 40, cy_server + 85)
    _box(draw, backend_box, "Backend — FastAPI (Python)",
         ["приём сообщений  ·  сессии  ·  LLM  ·  БД"], header=GREEN2)

    side_cx = (SIDE_L[0] + SIDE_L[1]) // 2
    parser_box = _hbox(side_cx, y_server + 130, SIDE_W - 60, 130)
    site_box = _hbox(side_cx, y_db + 120, SIDE_W - 60, 110)
    _box(draw, parser_box, "BeautifulSoup", ["requests + парсинг HTML"])
    _box(draw, site_box, "bon-voyage28.ru", ["источник каталога туров"], header=GRAY)

    ext_cx = (SIDE_R[0] + SIDE_R[1]) // 2
    llm_box = _hbox(ext_cx, cy_server, SIDE_W - 60, 170)
    _box(draw, llm_box, "GigaChat + DeepSeek",
         ["промпт + JSON-ответ", "fallback при сбое"], header=TEAL)

    # --- БД: 7 таблиц (2 ряда, как в ER-схеме) ---
    mysql_y = y_db + 168
    _cylinder(draw, CX, mysql_y, 200, 100, "MySQL")

    th = 62
    row1_y = y_db + 255
    row2_y = y_db + h_db - th - 48

    row1 = ["hotels", "flights", "daily_stats"]
    row2 = ["user_sessions", "user_queries", "generated_tours", "agency_leads"]

    row1_centers = _table_row(draw, row1, row1_y, 360, th, 44)
    row2_centers = _table_row(draw, row2, row2_y, 340, th, 36)
    table_centers = row1_centers + row2_centers

    hub_y = mysql_y + 52
    for cx in table_centers:
        if cy_mid := (row1_y if cx in row1_centers else row2_y):
            draw.line((cx, cy_mid, cx, hub_y), fill=GRAY, width=2)
    draw.line((min(table_centers), hub_y, max(table_centers), hub_y), fill=GRAY, width=2)
    draw.line((CX, hub_y, CX, mysql_y - 52), fill=GRAY, width=2)

    # --- Стрелки (ортогональные) ---
    user_r = user_box[2]
    frontend_l = frontend_box[0]
    mid_y_user = (user_box[1] + user_box[3]) // 2
    _line_arrow(draw, [(user_r, mid_y_user), (frontend_l, mid_y_user)])

    fe_cx = (frontend_box[0] + frontend_box[2]) // 2
    be_top = backend_box[1]
    _line_arrow(draw, [(fe_cx, frontend_box[3]), (fe_cx, be_top - 20), (CX, be_top - 20), (CX, be_top)],
                "HTTP/JSON  POST /api/chat", double=True)

    be_bot = backend_box[3]
    _line_arrow(draw, [(CX, be_bot), (CX, mysql_y - 58)], "SQL", double=True)

    be_r = backend_box[2]
    llm_l = llm_box[0]
    mid_y_be = (backend_box[1] + backend_box[3]) // 2
    _line_arrow(draw, [(be_r, mid_y_be), (llm_l, mid_y_be)], "HTTPS REST", double=True)

    parser_bot = parser_box[3]
    site_top = site_box[1]
    _line_arrow(draw, [(side_cx, parser_bot), (side_cx, site_top)])

    parser_r = parser_box[2]
    _line_arrow(draw, [(parser_r, (parser_box[1] + parser_box[3]) // 2),
                       (backend_box[0], mid_y_be)], "данные каталога")

    hotels_x = row1_centers[0]
    route_y = row1_y - 42
    _line_arrow(draw, [(side_cx, site_box[3]), (side_cx, route_y), (hotels_x, route_y), (hotels_x, row1_y)],
                "INSERT hotels")

    _center_text(draw, (CX, H - 42), "ООО «Бон Вояж»  ·  Планета 360  ·  tour-generator-module", _font(23), GRAY)

    img.save(OUT, "PNG", optimize=True)
    print(f"Saved: {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
