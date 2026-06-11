"""PNG-иллюстрации для презентации защиты диплома."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parent / "presentation_images"

GREEN = (1, 119, 58)
GREEN2 = (2, 138, 70)
TEAL = (13, 148, 136)
DARK = (30, 41, 59)
GRAY = (100, 116, 139)
LIGHT = (240, 253, 244)
BORDER = (187, 247, 208)
WHITE = (255, 255, 255)
SKY = (186, 230, 253)
SAND = (254, 243, 199)


def _font(size: int, bold: bool = False):
    paths = [
        ("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        ("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _grad(img: Image.Image, c1, c2, horiz: bool = False):
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = (x / max(w - 1, 1)) if horiz else (y / max(h - 1, 1))
            px[x, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _rr(draw, box, r=14, fill=WHITE, outline=None, w=2):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=w)


def _save(name: str, img: Image.Image) -> Path:
    ASSETS.mkdir(parents=True, exist_ok=True)
    p = ASSETS / name
    img.save(p, "PNG", optimize=True)
    return p


def _arrow(draw, x1, y1, x2, y2, color=GRAY):
    draw.line((x1, y1, x2, y2), fill=color, width=3)
    if abs(x2 - x1) >= abs(y2 - y1):
        s = 1 if x2 > x1 else -1
        draw.polygon([(x2, y2), (x2 - 12 * s, y2 - 6), (x2 - 12 * s, y2 + 6)], fill=color)
    else:
        s = 1 if y2 > y1 else -1
        draw.polygon([(x2, y2), (x2 - 6, y2 - 12 * s), (x2 + 6, y2 - 12 * s)], fill=color)


def make_cover() -> Path:
    img = Image.new("RGB", (1000, 680), GREEN)
    _grad(img, (1, 80, 45), TEAL, horiz=True)
    d = ImageDraw.Draw(img)
    d.ellipse((700, 40, 920, 260), fill=(255, 220, 100))
    d.rectangle((0, 460, 1000, 680), fill=(8, 100, 120))
    d.rectangle((0, 440, 1000, 470), fill=SAND)
    d.rectangle((90, 310, 110, 440), fill=(100, 60, 20))
    for ox, oy in [(-28, -18), (0, -32), (28, -18), (-14, -42), (14, -42)]:
        d.ellipse((98 + ox, 255 + oy, 138 + ox, 295 + oy), fill=GREEN2)
    d.polygon([(560, 170), (700, 195), (560, 220), (585, 195)], fill=WHITE)
    d.text((48, 48), "Планета 360  ·  Бон Вояж", fill=WHITE, font=_font(28, True))
    d.text((48, 100), "AI Тур-Генератор", fill=BORDER, font=_font(20, True))
    d.text((48, 560), "Дипломный проект 09.02.07", fill=WHITE, font=_font(18))
    return _save("cover.png", img)


def make_relevance() -> Path:
    img = Image.new("RGB", (900, 520), LIGHT)
    d = ImageDraw.Draw(img)
    _rr(d, (16, 16, 884, 504), 20, WHITE, GREEN, 2)
    d.text((36, 30), "Почему это актуально?", fill=GREEN, font=_font(24, True))
    items = [
        ("24/7", "Клиенты хотят подбирать туры\nбез ожидания менеджера"),
        ("Текст", "Свободная формулировка запроса\nудобнее длинных форм"),
        ("ИИ", "LLM извлекает даты, бюджет\nи направление из диалога"),
        ("Бизнес", "Снижение нагрузки на менеджеров\nи рост конверсии заявок"),
    ]
    x = 40
    for badge, text in items:
        _rr(d, (x, 90, x + 190, 460), 16, LIGHT, BORDER, 2)
        _rr(d, (x + 14, 110, x + 90, 150), 10, GREEN)
        d.text((x + 28, 118), badge, fill=WHITE, font=_font(14, True))
        d.multiline_text((x + 14, 175), text, fill=DARK, font=_font(14), spacing=6)
        x += 210
    return _save("relevance.png", img)


def make_architecture() -> Path:
    img = Image.new("RGB", (980, 560), WHITE)
    d = ImageDraw.Draw(img)
    d.text((30, 18), "Архитектура модуля", fill=GREEN, font=_font(24, True))

    def block(x, y, w, h, title, lines, color):
        _rr(d, (x, y, x + w, y + h), 14, WHITE, color, 3)
        _rr(d, (x, y, x + w, y + 42), 14, color)
        d.rectangle((x, y + 22, x + w, y + 42), fill=color)
        d.text((x + 14, y + 10), title, fill=WHITE, font=_font(15, True))
        ty = y + 56
        for ln in lines:
            d.text((x + 14, ty), ln, fill=DARK, font=_font(13))
            ty += 22

    block(40, 70, 210, 120, "Клиент", ["Vue.js SPA", "Чат-интерфейс", "Карточка тура"], TEAL)
    block(370, 70, 240, 140, "Сервер FastAPI", ["app.py /api/chat", "ai_service.py", "date_validation"], GREEN)
    block(720, 70, 220, 120, "Нейросети", ["GigaChat (Сбер)", "DeepSeek API", "режим auto"], DARK)
    _arrow(d, 250, 130, 370, 130, GREEN)
    _arrow(d, 610, 130, 720, 130, GREEN)

    block(370, 260, 240, 110, "MySQL 8.0", ["hotels, sessions", "queries, leads"], GREEN2)
    block(80, 260, 200, 110, "Парсер", ["bon-voyage28.ru", "каталог туров"], GRAY)
    _arrow(d, 280, 315, 370, 315, TEAL)
    _arrow(d, 490, 210, 490, 260, TEAL)

    _rr(d, (80, 410, 900, 530), 16, LIGHT, GREEN, 2)
    d.text((100, 430), "Поток: запрос → LLM → параметры → БД → турпакет → ответ клиенту", fill=DARK, font=_font(15))
    return _save("architecture.png", img)


def make_idef0() -> Path:
    img = Image.new("RGB", (980, 520), WHITE)
    d = ImageDraw.Draw(img)
    d.text((30, 16), "IDEF0 — турфирма «Бон Вояж»", fill=GREEN, font=_font(22, True))
    blocks = [
        (50, 80, 160, 85, "A1", "Планирование\nпоездки", GREEN),
        (250, 80, 160, 85, "A2", "Формирование\nгруппы", GREEN2),
        (450, 80, 160, 85, "A3", "Логистика", TEAL),
        (650, 80, 160, 85, "A4", "Сопровождение", DARK),
        (350, 210, 180, 85, "A5", "Отчётность", GRAY),
    ]
    for x, y, w, h, code, label, col in blocks:
        _rr(d, (x, y, x + w, y + h), 12, col)
        d.text((x + 12, y + 10), code, fill=WHITE, font=_font(13, True))
        d.multiline_text((x + 12, y + 32), label, fill=WHITE, font=_font(12), spacing=4)
    _arrow(d, 210, 122, 250, 122)
    _arrow(d, 410, 122, 450, 122)
    _arrow(d, 610, 122, 650, 122)
    _arrow(d, 530, 165, 440, 210)
    _rr(d, (50, 340, 930, 480), 16, LIGHT, GREEN, 3)
    d.text((70, 365), "Модуль AI Тур-Генератор", fill=GREEN, font=_font(20, True))
    d.text((70, 405), "Автоматизирует этап A1 — первичный подбор тура по текстовому запросу на сайте", fill=DARK, font=_font(15))
    return _save("idef0.png", img)


def make_database() -> Path:
    img = Image.new("RGB", (980, 540), LIGHT)
    d = ImageDraw.Draw(img)
    d.text((30, 16), "База данных MySQL", fill=GREEN, font=_font(22, True))

    tables = [
        (40, 70, "hotels", ["id, name", "country, price", "source_site"]),
        (350, 70, "user_sessions", ["session_id", "state JSON", "updated_at"]),
        (660, 70, "user_queries", ["id", "session_id", "user_input"]),
        (40, 260, "generated_tours", ["id", "tour JSON", "total_price"]),
        (350, 260, "agency_leads", ["name, phone", "email, message"]),
        (660, 260, "daily_stats", ["date", "queries", "tours, leads"]),
    ]
    for x, y, name, cols in tables:
        _rr(d, (x, y, x + 270, y + 160), 12, WHITE, GREEN, 2)
        _rr(d, (x, y, x + 270, y + 38), 12, GREEN)
        d.rectangle((x, y + 20, x + 270, y + 38), fill=GREEN)
        d.text((x + 12, y + 8), name, fill=WHITE, font=_font(14, True))
        cy = y + 52
        for c in cols:
            d.text((x + 12, cy), c, fill=DARK, font=_font(13))
            cy += 24
    _arrow(d, 310, 150, 350, 150, GREEN)
    _arrow(d, 620, 150, 660, 150, GREEN)
    return _save("database.png", img)


def make_ai_flow() -> Path:
    img = Image.new("RGB", (980, 540), WHITE)
    d = ImageDraw.Draw(img)
    d.text((30, 16), "Алгоритм AI-агента", fill=GREEN, font=_font(22, True))

    def step(x, y, title, body, col):
        _rr(d, (x, y, x + 210, y + 105), 14, col)
        d.text((x + 14, y + 12), title, fill=WHITE, font=_font(14, True))
        d.multiline_text((x + 14, y + 38), body, fill=WHITE, font=_font(12), spacing=4)

    step(50, 70, "1. Старт", "POST /api/chat\nновое сообщение", GREEN)
    step(310, 70, "2. Фаза 1", "Диалог LLM\nсбор параметров", TEAL)
    step(570, 70, "3. Проверка", "date_validation\nдаты и бюджет", GREEN2)
    step(50, 230, "4. Поиск", "SELECT hotels\nиз MySQL", GRAY)
    step(310, 230, "5. Фаза 2", "LLM формирует\nтурпакет", TEAL)
    step(570, 230, "6. Fallback", "GigaChat →\nDeepSeek", DARK)
    step(310, 390, "7. Ответ", "Карточка тура\nв чате", GREEN)

    _arrow(d, 260, 122, 310, 122)
    _arrow(d, 520, 122, 570, 122)
    _arrow(d, 675, 175, 675, 230)
    _arrow(d, 675, 230, 155, 280)
    _arrow(d, 260, 282, 310, 282)
    _arrow(d, 520, 282, 570, 282)
    _arrow(d, 415, 335, 415, 390)
    return _save("ai_flow.png", img)


def make_ui() -> Path:
    img = Image.new("RGB", (980, 620), (248, 250, 252))
    header = Image.new("RGB", (980, 72), GREEN)
    _grad(header, GREEN, GREEN2, horiz=True)
    img.paste(header, (0, 0))
    d = ImageDraw.Draw(img)
    d.text((28, 22), "Планета 360", fill=WHITE, font=_font(22, True))
    d.text((720, 26), "+7 (4162) 317-771", fill=WHITE, font=_font(14))

    _rr(d, (28, 92, 952, 590), 22, WHITE, BORDER, 2)
    _rr(d, (28, 92, 952, 155), 22, GREEN)
    d.rectangle((28, 125, 952, 155), fill=GREEN)
    d.text((48, 108), "AI Тур-Генератор", fill=WHITE, font=_font(20, True))
    d.text((48, 170), "Расскажите направление, даты и бюджет — нейросеть подберёт тур", fill=GRAY, font=_font(13))

    _rr(d, (48, 200, 932, 240), 10, LIGHT, BORDER, 1)
    d.text((62, 212), "Нейросеть: Auto (GigaChat + DeepSeek)", fill=DARK, font=_font(13))

    _rr(d, (500, 260, 920, 315), 14, SKY)
    d.text((520, 275), "Хочу в Китай 10–20 июля, бюджет 80 000 ₽", fill=DARK, font=_font(13))

    _rr(d, (48, 335, 650, 470), 14, LIGHT, GREEN, 2)
    d.text((62, 350), "DeepSeek", fill=GREEN, font=_font(11, True))
    d.text((62, 372), "Подбираю тур в Китай на указанные даты…", fill=DARK, font=_font(13))

    _rr(d, (62, 400, 630, 520), 12, WHITE, TEAL, 2)
    d.text((78, 414), "Тур в Китай · Пекин", fill=GREEN, font=_font(14, True))
    d.text((78, 440), "Отель Beijing Grand 4★", fill=DARK, font=_font(12))
    d.text((78, 462), "Перелёт 10–20 июля", fill=DARK, font=_font(12))
    d.text((78, 488), "Итого: 78 500 ₽", fill=GREEN, font=_font(16, True))

    _rr(d, (48, 535, 760, 575), 12, WHITE, BORDER, 2)
    d.text((62, 548), "Введите запрос…", fill=GRAY, font=_font(13))
    _rr(d, (780, 535, 932, 575), 12, GREEN)
    d.text((808, 548), "Отправить", fill=WHITE, font=_font(13, True))
    return _save("ui.png", img)


def make_economy() -> Path:
    img = Image.new("RGB", (980, 520), LIGHT)
    d = ImageDraw.Draw(img)
    d.text((30, 16), "Экономическое обоснование", fill=GREEN, font=_font(22, True))
    cards = [
        (40, 75, "107 720 ₽", "Затраты на\nразработку", GREEN),
        (270, 75, "47 100 ₽", "Эксплуатация\nв год", GRAY),
        (500, 75, "711 300 ₽", "Чистый эффект\nв год", TEAL),
        (730, 75, "~2 мес.", "Окупаемость", GREEN2),
    ]
    for x, y, val, lbl, col in cards:
        _rr(d, (x, y, x + 210, y + 155), 16, WHITE, col, 3)
        d.text((x + 16, y + 22), val, fill=col, font=_font(22, True))
        d.multiline_text((x + 16, y + 72), lbl, fill=DARK, font=_font(14), spacing=4)

    _rr(d, (40, 270, 940, 480), 18, WHITE, GREEN, 3)
    d.text((60, 295), "Kэф = 6,6", fill=GREEN, font=_font(36, True))
    d.text((60, 350), "Модуль работает круглосуточно, снижает нагрузку на менеджеров", fill=DARK, font=_font(15))
    d.text((60, 380), "и увеличивает число обработанных заявок без найма дополнительного персонала.", fill=DARK, font=_font(15))

    bars = [70, 100, 180, 320]
    labels = ["Затраты", "Экспл.", "Эффект", "Прибыль"]
    colors = [GRAY, GREEN2, TEAL, GREEN]
    bx = 560
    for i, (h, lb, col) in enumerate(zip(bars, labels, colors)):
        _rr(d, (bx + i * 85, 430 - h, bx + i * 85 + 60, 430), 8, col)
        d.text((bx + i * 85 + 6, 438), lb, fill=GRAY, font=_font(10))
    return _save("economy.png", img)


def make_testing() -> Path:
    img = Image.new("RGB", (900, 480), WHITE)
    d = ImageDraw.Draw(img)
    d.text((30, 18), "Тестирование модуля", fill=GREEN, font=_font(22, True))
    rows = [
        ("Модульное", "test_dates.py", "Валидация дат поездки", GREEN),
        ("Интеграционное", "test_deepseek.py", "Запросы к DeepSeek API", TEAL),
        ("Интеграционное", "test_gigachat.py", "Запросы к GigaChat", GREEN2),
        ("Функциональное", "Диалог end-to-end", "Запрос → турпакет → заявка", DARK),
    ]
    y = 75
    for kind, script, desc, col in rows:
        _rr(d, (30, y, 870, y + 85), 14, LIGHT, col, 2)
        _rr(d, (40, y + 12, 180, y + 42), 8, col)
        d.text((52, y + 18), kind, fill=WHITE, font=_font(12, True))
        d.text((240, y + 18), script, fill=DARK, font=_font(14, True))
        d.text((240, y + 46), desc, fill=GRAY, font=_font(13))
        y += 95
    return _save("testing.png", img)


def generate_all() -> dict[str, Path]:
    return {
        "cover": make_cover(),
        "relevance": make_relevance(),
        "architecture": make_architecture(),
        "idef0": make_idef0(),
        "database": make_database(),
        "ai_flow": make_ai_flow(),
        "ui": make_ui(),
        "economy": make_economy(),
        "testing": make_testing(),
    }


if __name__ == "__main__":
    for k, p in generate_all().items():
        print(f"{k}: {p}")
