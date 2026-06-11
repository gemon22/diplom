"""
Презентация для защиты диплома — только текст, без картинок.
Запуск:  python docs/build_defense_presentation.py
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

DOCS = Path(__file__).resolve().parent
OUT = DOCS / "Диплом_защита_презентация.pptx"

G, G2, T = "01773A", "028A46", "0D9488"
DK, GR, LT, BD, WH = "1E293B", "64748B", "F0FDF4", "BBF7D0", "FFFFFF"

# body  — основные пункты слева
# detail — подробный текст справа (то, что раньше было на картинках)
SLIDES = [
    {
        "kind": "title",
        "title": "Модуль динамической генерации турпакета\nна основе методов искусственного интеллекта",
        "body": [
            "Студент: ФИО",
            "Группа: ______",
            "Специальность: 09.02.07 Информационные системы и программирование",
            "Руководитель: ФИО",
            "ГБПОУ «Амурский технический колледж» · 2026",
        ],
        "notes": "Здравствуйте. Представляю дипломный проект — модуль AI-подбора туров для «Бон Вояж» / «Планета 360».",
    },
    {
        "title": "Актуальность темы",
        "body": [
            "Клиенты турфирм ожидают быстрый онлайн-подбор",
            "Свободный текст удобнее форм и фильтров",
            "LLM понимают запрос на русском языке",
            "Автоматизация работает 24/7 без выходных",
        ],
        "detail": [
            "ПРОБЛЕМА",
            "Менеджер не всегда может ответить сразу — клиент уходит к конкурентам.",
            "",
            "РЕШЕНИЕ",
            "Модуль принимает запрос в свободной форме:",
            "«Хочу в Китай с 10 по 20 июля, бюджет 80 000 руб.»",
            "",
            "ВЫГОДА",
            "Снижение нагрузки на сотрудников, рост числа заявок.",
        ],
        "notes": "Почему тема важна для турфирмы в Благовещенске.",
    },
    {
        "title": "Цель и задачи проекта",
        "body": [
            "Цель: разработать модуль генерации турпакета на основе ИИ",
            "Изучить применение LLM в туризме",
            "Спроектировать архитектуру, БД и AI-агента",
            "Реализовать интерфейс, сервер и парсер",
            "Интегрировать DeepSeek и GigaChat",
            "Провести тестирование и экономическое обоснование",
        ],
        "numbered": True,
        "notes": "Цель — одним предложением, задачи по заданию.",
    },
    {
        "title": "Объект и предмет исследования",
        "body": [
            "Объект: процесс подбора турпакета в турфирме",
            "Предмет: методы применения ИИ для генерации турпакета",
            "База практики: ООО «Бон Вояж», bon-voyage28.ru",
            "Результат: модуль для сайта «Планета 360»",
        ],
        "notes": "Классический слайд защиты.",
    },
    {
        "title": "Средства разработки",
        "body": [
            "Python 3.11 — основной язык",
            "FastAPI + Uvicorn — сервер",
            "Vue.js — клиентский интерфейс",
            "MySQL 8.0 — база данных",
            "DeepSeek API, GigaChat — LLM",
            "BeautifulSoup — парсер каталога",
        ],
        "detail": [
            "СТЕК ТЕХНОЛОГИЙ",
            "Backend:  app.py, ai_service.py, config.py",
            "Frontend: frontend/index.html (Vue SPA)",
            "Парсер:   parser.py → таблица hotels",
            "Конфиг:   .env + requirements.txt",
            "Запуск:   python run_server.py",
            "Адрес:    http://localhost:8000",
        ],
        "notes": "Назовите стек и основные файлы проекта.",
    },
    {
        "title": "Архитектура системы",
        "body": [
            "Клиент-серверная архитектура",
            "Три уровня: клиент → сервер → данные",
            "Два провайдера ИИ с fallback",
        ],
        "detail": [
            "КЛИЕНТ (Vue.js)",
            "· Чат-интерфейс, выбор LLM",
            "· Карточка готового турпакета",
            "· Форма заявки менеджеру",
            "",
            "СЕРВЕР (FastAPI)",
            "· POST /api/chat — основной эндпоинт",
            "· ai_service.py — логика AI-агента",
            "· date_validation.py — проверка дат",
            "",
            "ДАННЫЕ",
            "· MySQL — каталог, сессии, заявки",
            "· GigaChat / DeepSeek — нейросети",
            "",
            "ПОТОК",
            "Запрос → LLM → параметры → БД → турпакет → ответ",
        ],
        "notes": "Опишите поток данных словами.",
    },
    {
        "title": "Бизнес-процесс (IDEF0)",
        "body": [
            "Деятельность турфирмы «Бон Вояж»",
            "5 этапов: A1 → A2 → A3 → A4 → A5",
            "Модуль автоматизирует этап A1",
        ],
        "detail": [
            "A1 — Планирование поездки",
            "   Первичный подбор направления и тура",
            "   ← МОДУЛЬ АВТОМАТИЗИРУЕТ ЭТОТ ЭТАП",
            "",
            "A2 — Формирование группы",
            "A3 — Организация логистики",
            "A4 — Сопровождение туристов",
            "A5 — Отчётность и анализ",
            "",
            "Вход: запрос клиента на сайте",
            "Выход: готовый турпакет + заявка",
        ],
        "notes": "Связь с бизнес-процессом организации.",
    },
    {
        "title": "База данных MySQL",
        "body": [
            "6 таблиц в единой схеме",
            "Каталог, сессии, история, заявки",
            "Состояние диалога хранится в JSON",
        ],
        "detail": [
            "hotels",
            "  Каталог туров (парсер bon-voyage28.ru)",
            "  name, country, price, dates",
            "",
            "user_sessions",
            "  session_id, state (JSON), updated_at",
            "",
            "user_queries / generated_tours",
            "  История сообщений и турпакетов",
            "",
            "agency_leads / daily_stats",
            "  Заявки клиентов и статистика",
        ],
        "notes": "Таблицы из database.py.",
    },
    {
        "title": "Алгоритм AI-агента",
        "body": [
            "Двухфазный алгоритм",
            "Серверная валидация параметров",
            "Отказоустойчивость при сбое LLM",
        ],
        "detail": [
            "1. Старт — POST /api/chat",
            "2. Фаза 1 — диалог LLM:",
            "   сбор направления, дат, бюджета",
            "3. Валидация — date_validation.py",
            "4. Поиск — SELECT из таблицы hotels",
            "5. Фаза 2 — LLM формирует турпакет",
            "6. Fallback — GigaChat → DeepSeek",
            "7. Ответ — карточка тура в чате",
            "",
            "Режим auto: сначала GigaChat,",
            "при ошибке — автоматически DeepSeek",
        ],
        "notes": "Ключевой слайд. Можно показать демо.",
    },
    {
        "title": "Клиентский интерфейс",
        "body": [
            "Веб-чат на Vue.js",
            "Свободный ввод на русском языке",
            "Карточка тура и форма заявки",
        ],
        "detail": [
            "ШАПКА САЙТА",
            "· Логотип «Планета 360»",
            "· Навигация, телефон турфирмы",
            "",
            "МОДУЛЬ «AI Тур-Генератор»",
            "· Выбор нейросети: Auto / GigaChat / DeepSeek",
            "· Поле ввода: «Хочу в Китай…»",
            "· Кнопки: Отправить, Сброс",
            "",
            "КАРТОЧКА ТУРА",
            "· Отель, перелёт, даты, цена",
            "· Кнопки: «Купить» / «Страница турфирмы»",
            "",
            "ЗАЯВКА: имя, телефон, email → менеджеру",
        ],
        "notes": "Демо: http://localhost:8000",
    },
    {
        "title": "Тестирование",
        "body": [
            "Модульное, интеграционное, функциональное",
            "Все сценарии пройдены успешно",
        ],
        "detail": [
            "МОДУЛЬНОЕ",
            "· test_dates.py — валидация дат поездки",
            "",
            "ИНТЕГРАЦИОННОЕ",
            "· test_deepseek.py — API DeepSeek",
            "· test_gigachat.py — API GigaChat",
            "",
            "ФУНКЦИОНАЛЬНОЕ",
            "· Полный диалог → турпакет",
            "· Fallback при сбое GigaChat",
            "· Сброс сессии (POST /api/reset)",
            "· Сохранение заявки в agency_leads",
        ],
        "notes": "Результаты в главе 3.4.",
    },
    {
        "title": "Экономическое обоснование",
        "body": [
            "Затраты на разработку: 107 720 руб.",
            "Эксплуатация: 47 100 руб./год",
            "Чистый эффект: 711 300 руб./год",
        ],
        "detail": [
            "ЗАТРАТЫ НА РАЗРАБОТКУ",
            "· 200 ч × 500 руб./ч = 100 000 руб.",
            "· Материалы и хостинг = 7 720 руб.",
            "· Итого: 107 720 руб.",
            "",
            "ЭФФЕКТ В ГОД",
            "· Экономия времени менеджеров",
            "· Дополнительные заявки с сайта",
            "· Чистый эффект: 711 300 руб./год",
            "",
            "Окупаемость: ~2 месяца",
            "Коэффициент эффективности Kэф = 6,6",
        ],
        "notes": "Цифры из главы 5.",
    },
    {
        "title": "Результаты работы",
        "body": [
            "Разработан модуль «AI Тур-Генератор»",
            "Диалог на русском, реальный каталог",
            "Двухпровайдерная схема ИИ",
            "Готов к внедрению на bon-voyage28.ru",
        ],
        "notes": "Работающий прототип.",
    },
    {
        "title": "Выводы",
        "body": [
            "Цель дипломного проекта достигнута",
            "Все задачи выполнены в полном объёме",
            "Модуль снижает нагрузку на менеджеров",
            "Экономическая эффективность подтверждена",
        ],
        "notes": "30 секунд. Уверенный финал.",
    },
    {
        "kind": "end",
        "title": "Спасибо за внимание!",
        "body": [
            "Готов ответить на ваши вопросы",
            "Демонстрация: http://localhost:8000",
            "Турфирма «Бон Вояж»: +7 (4162) 317-771",
        ],
        "notes": "Вопросы комиссии.",
    },
]


def _run(text: str, sz: int = 1700, bold: bool = False, color: str = DK) -> str:
    b = ' b="1"' if bold else ""
    return (
        f'<a:r><a:rPr sz="{sz}"{b}><a:solidFill><a:srgbClr val="{color}"/>'
        f'</a:solidFill><a:latin typeface="Calibri"/></a:rPr>'
        f'<a:t>{escape(text)}</a:t></a:r>'
    )


def _para(text: str, sz: int = 1700, bold: bool = False, color: str = DK, align: str = "l", space: int = 0) -> str:
    spc = f' spcAft="{space}"' if space else ""
    return f'<a:p><a:pPr algn="{align}"{spc}/>{_run(text, sz, bold, color)}</a:p>'


def _title(text: str, sz: int = 2550, color: str = G, align: str = "l") -> str:
    parts = []
    for i, ln in enumerate(text.split("\n")):
        br = "<a:br/>" if i else ""
        parts.append(
            f'<a:r><a:rPr sz="{sz}" b="1"><a:solidFill><a:srgbClr val="{color}"/>'
            f'</a:solidFill><a:latin typeface="Calibri Light"/></a:rPr>'
            f'<a:t>{br}{escape(ln)}</a:t></a:r>'
        )
    return f'<a:p><a:pPr algn="{align}"/>{"".join(parts)}</a:p>'


def _bullet(text: str, sz: int = 1650, color: str = DK, num: int = 0) -> str:
    if num:
        ppr = f'<a:pPr marL="360000" indent="-180000" spcAft="700"><a:buAutoNum type="arabicPeriod" startAt="{num}"/></a:pPr>'
    else:
        ppr = '<a:pPr marL="280000" indent="-140000" spcAft="700"><a:buChar char="●"/></a:pPr>'
    return f'<a:p>{ppr}{_run(text, sz, color=color)}</a:p>'


def _detail_line(line: str) -> str:
    if not line:
        return '<a:p><a:pPr spcAft="200"/></a:p>'
    if line.isupper() and len(line) < 40:
        return _para(line, 1500, True, G, space=400)
    if line.startswith("·") or line.startswith("←"):
        return _para(line, 1450, color=DK, space=100)
    if line.startswith("  "):
        return _para(line.strip(), 1400, color=GR, space=80)
    return _para(line, 1450, color=DK, space=120)


def _body_xml(sl: dict, sz: int, color: str) -> str:
    xml = ""
    for i, ln in enumerate(sl.get("body", []), 1):
        xml += _bullet(ln, sz, color, i if sl.get("numbered") else 0)
    return xml


def _detail_xml(lines: list[str]) -> str:
    return "".join(_detail_line(ln) for ln in lines)


def _rect(sid, name, x, y, cx, cy, fill=None, alpha=None, r=None, line=None):
    if line:
        geom = f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val {r or 8000}"/></a:avLst></a:prstGeom>' if r else '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        return f"""<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>{geom}
<a:noFill/><a:ln w="12700"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln></p:spPr>
<p:txBody><a:bodyPr/><a:lstStyle/></p:txBody></p:sp>"""
    fill_xml = f'<a:solidFill><a:srgbClr val="{fill}">'
    if alpha:
        fill_xml += f'<a:alpha val="{alpha}"/>'
    fill_xml += "</a:srgbClr></a:solidFill>"
    geom = f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val {r or 8000}"/></a:avLst></a:prstGeom>' if r else '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
    return f"""<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>{geom}{fill_xml}
<a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/></p:txBody></p:sp>"""


def _ellipse(sid, name, x, y, cx, cy, fill, alpha=None):
    fill_xml = f'<a:solidFill><a:srgbClr val="{fill}">'
    if alpha:
        fill_xml += f'<a:alpha val="{alpha}"/>'
    fill_xml += "</a:srgbClr></a:solidFill>"
    return f"""<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>{fill_xml}<a:ln><a:noFill/></a:ln></p:spPr>
<p:txBody><a:bodyPr/><a:lstStyle/></p:txBody></p:sp>"""


def _text(sid, name, x, y, cx, cy, xml, anchor="t"):
    return f"""<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
<p:txBody><a:bodyPr anchor="{anchor}" wrap="square" lIns="91440" tIns="45720" rIns="91440" bIns="45720"/>
<a:lstStyle/>{xml}</p:txBody></p:sp>"""


def _grad_bg():
    return (
        f"<p:bg><p:bgPr><a:gradFill rotWithShape=\"1\"><a:gsLst>"
        f"<a:gs pos=\"0\"><a:srgbClr val=\"{G}\"/></a:gs>"
        f"<a:gs pos=\"55000\"><a:srgbClr val=\"{G2}\"/></a:gs>"
        f"<a:gs pos=\"100000\"><a:srgbClr val=\"{T}\"/></a:gs>"
        f"</a:gsLst><a:lin ang=\"5400000\" scaled=\"1\"/></a:gradFill>"
        f"<a:effectLst/></p:bgPr></p:bg>"
    )


def _white_bg():
    return f"<p:bg><p:bgPr><a:solidFill><a:srgbClr val=\"{WH}\"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>"


def _decor(num: int, kind: str | None, two_col: bool) -> str:
    if kind in ("title", "end"):
        return "\n".join([
            _ellipse(10, "c1", 9200000, -200000, 3200000, 3200000, WH, 10000),
            _ellipse(11, "c2", -400000, 4600000, 2200000, 2200000, WH, 8000),
            _rect(12, "badge", 2600000, 300000, 7000000, 400000, WH, 18000, 12000),
            _text(13, "badgeT", 2600000, 330000, 7000000, 340000,
                  _para("Дипломный проект  ·  09.02.07  ·  Бон Вояж", 1400, True, WH, "ctr"), "ctr"),
            _text(14, "logo", 360000, 150000, 4500000, 300000,
                  _para("✈  AI Тур-Генератор", 1800, True, WH)),
        ])

    parts = [
        _rect(10, "hdr", 0, 0, 12192000, 500000, G),
        _text(11, "hdr1", 360000, 100000, 5000000, 300000, _para("✈  AI Тур-Генератор", 1500, True, WH)),
        _text(12, "hdr2", 7400000, 120000, 4400000, 260000,
              _para("Защита диплома · 09.02.07", 1150, color=BD, align="r"), "ctr"),
        _rect(13, "stripe", 0, 500000, 90000, 5800000, G2),
        _rect(17, "ul", 560000, 1000000, 2800000, 40000, G),
        _rect(18, "ftr", 0, 6320000, 12192000, 538000, DK),
        _text(19, "ftrL", 360000, 6390000, 5000000, 260000, _para("bon-voyage28.ru · Планета 360", 1100, color=BD)),
        _text(20, "ftrR", 9200000, 6390000, 2400000, 260000,
              _para(f"{num} / {len(SLIDES)}", 1200, True, WH, "r"), "ctr"),
    ]
    if two_col:
        parts += [
            _rect(15, "leftC", 480000, 1120000, 4800000, 5000000, LT, r=8000),
            _rect(16, "rightC", 5400000, 1120000, 6200000, 5000000, WH, r=8000),
            _rect(21, "rightB", 5400000, 1120000, 6200000, 5000000, line=BD, r=8000),
        ]
    else:
        parts += [
            _rect(15, "card", 480000, 1120000, 11000000, 5000000, LT, r=8000),
            _rect(16, "cardB", 480000, 1120000, 11000000, 5000000, line=BD, r=8000),
        ]
    return "\n".join(parts)


def _slide_xml(sl: dict, num: int) -> str:
    kind = sl.get("kind")
    special = kind in ("title", "end")
    two_col = bool(sl.get("detail")) and not special

    t_color = WH if special else G
    b_color = WH if special else DK
    t_sz = 2600 if kind == "title" else (3000 if kind == "end" else 2400)
    b_sz = 1700 if special else 1620

    title_xml = _title(sl["title"], t_sz, t_color, "ctr" if special else "l")
    body_xml = _body_xml(sl, b_sz, b_color)

    bg = _grad_bg() if special else _white_bg()
    decor = _decor(num, kind, two_col)

    shapes = [decor]

    if special:
        shapes.append(_text(2, "Title", 700000, 1850000, 10800000, 2200000, title_xml, "ctr"))
        shapes.append(_text(3, "Body", 1200000, 4200000, 9800000, 1900000, body_xml, "ctr"))
    elif two_col:
        shapes.append(_text(2, "Title", 560000, 1040000, 10500000, 380000, title_xml))
        shapes.append(_text(3, "Body", 600000, 1200000, 4600000, 4800000, body_xml))
        shapes.append(_text(4, "Detail", 5520000, 1180000, 6000000, 4900000, _detail_xml(sl["detail"])))
    else:
        shapes.append(_text(2, "Title", 600000, 1040000, 10500000, 380000, title_xml))
        shapes.append(_text(3, "Body", 680000, 1200000, 10400000, 4900000, body_xml))

    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld name="Slide {num}">{bg}<p:spTree>
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/></a:xfrm></p:grpSpPr>
{"".join(shapes)}
</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"""


def _notes(text: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:notes xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/></a:xfrm></p:grpSpPr>
<p:sp><p:nvSpPr><p:cNvPr id="2" name="N"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="685800" y="434340"/><a:ext cx="5486400" cy="4114800"/></a:xfrm></p:spPr>
<p:txBody><a:bodyPr/><a:lstStyle/>{_para(text, 1800)}</p:txBody></p:sp>
</p:spTree></p:cSld></p:notes>"""


def build(path: Path) -> None:
    n = len(SLIDES)
    pres_rels = [
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>',
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>',
    ] + [
        f'<Relationship Id="rId{i+2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        for i in range(1, n + 1)
    ]

    ctypes = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
        '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
    ]
    for i in range(1, n + 1):
        ctypes.append(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
        ctypes.append(f'<Override PartName="/ppt/notesSlides/notesSlide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>')
    ctypes.append("</Types>")

    sld_ids = "".join(f'<p:sldId id="{256+i}" r:id="rId{i+2}"/>' for i in range(1, n + 1))

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "\n".join(ctypes))
        z.writestr("_rels/.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>')
        z.writestr("ppt/presentation.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
<p:sldIdLst>{sld_ids}</p:sldIdLst>
<p:sldSz cx="12192000" cy="6858000" type="screen16x9"/><p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>""")
        z.writestr("ppt/_rels/presentation.xml.rels", f'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{chr(10).join(pres_rels)}</Relationships>')
        z.writestr("ppt/slideMasters/slideMaster1.xml", f"""<?xml version="1.0"?><p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="{WH}"/></a:solidFill></p:bgPr></p:bg>
<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst></p:sldMaster>""")
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>')
        z.writestr("ppt/slideLayouts/slideLayout1.xml", '<?xml version="1.0"?><p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>')
        z.writestr("ppt/theme/theme1.xml", f"""<?xml version="1.0"?><a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="BonVoyage">
<a:themeElements><a:clrScheme name="BV">
<a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1><a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
<a:dk2><a:srgbClr val="{DK}"/></a:dk2><a:lt2><a:srgbClr val="{LT}"/></a:lt2>
<a:accent1><a:srgbClr val="{G}"/></a:accent1><a:accent2><a:srgbClr val="{T}"/></a:accent2>
<a:accent3><a:srgbClr val="{G2}"/></a:accent3><a:accent4><a:srgbClr val="{GR}"/></a:accent4>
<a:accent5><a:srgbClr val="{BD}"/></a:accent5><a:accent6><a:srgbClr val="{DK}"/></a:accent6>
<a:hlink><a:srgbClr val="{G}"/></a:hlink><a:folHlink><a:srgbClr val="{GR}"/></a:folHlink>
</a:clrScheme><a:fontScheme name="Office"><a:majorFont><a:latin typeface="Calibri Light"/></a:majorFont><a:minorFont><a:latin typeface="Calibri"/></a:minorFont></a:fontScheme>
<a:fmtScheme name="Office"><a:fillStyleLst/><a:lnStyleLst/><a:effectStyleLst/><a:bgFillStyleLst/></a:fmtScheme>
</a:themeElements></a:theme>""")

        for i, sl in enumerate(SLIDES, 1):
            rels = [
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>',
                f'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" Target="../notesSlides/notesSlide{i}.xml"/>',
            ]
            z.writestr(f"ppt/slides/slide{i}.xml", _slide_xml(sl, i))
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", f'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{chr(10).join(rels)}</Relationships>')
            z.writestr(f"ppt/notesSlides/notesSlide{i}.xml", _notes(sl.get("notes", "")))
            z.writestr(f"ppt/notesSlides/_rels/notesSlide{i}.xml.rels", f'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster" Target="../notesMasters/notesMaster1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="../slides/slide{i}.xml"/></Relationships>')

        z.writestr("ppt/notesMasters/notesMaster1.xml", '<?xml version="1.0"?><p:notesMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld></p:notesMaster>')
        z.writestr("ppt/notesMasters/_rels/notesMaster1.xml.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>')


def main():
    build(OUT)
    copy = DOCS / "Diploma_Defense.pptx"
    copy.write_bytes(OUT.read_bytes())
    print(f"Готово: {OUT}")
    print(f"Копия:  {copy}")
    print(f"Слайдов: {len(SLIDES)} (только текст, без картинок)")


if __name__ == "__main__":
    main()
