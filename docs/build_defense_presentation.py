"""
Презентация для защиты диплома.
Запуск:  python docs/build_defense_presentation.py
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

DOCS = Path(__file__).resolve().parent
OUT = DOCS / "Диплом_защита_презентация.pptx"
DB_SCHEMA = DOCS / "db_schema.png"

G, G2, T = "01773A", "028A46", "0D9488"
DK, GR, LT, BD, WH = "1E293B", "64748B", "F0FDF4", "BBF7D0", "FFFFFF"

SLIDES = [
    {
        "kind": "title",
        "title": "Проектирование и разработка системы\nдинамической сборки турпакетов\nна основе методов искусственного интеллекта",
        "body": [
            "Студент: Ю.В. Тымченко",
            "Специальность: 09.02.07 — Информатика, программирование и эксплуатация БАС",
            "База практики: ООО «Бон Вояж»",
            "Руководитель: Д.П. Бардин",
            "ГБПОУ «Благовещенский политехнический колледж» · 2026",
        ],
        "notes": "Здравствуйте, уважаемые члены комиссии. Представляю ВКР — систему «AI Тур-Генератор» для ООО «Бон Вояж» (сайт Планета 360 / bon-voyage28.ru).",
    },
    {
        "title": "Актуальность темы",
        "body": [
            "Рост спроса на персонализированные туры",
            "Клиенты тратят часы на поиск на сайтах операторов",
            "Менеджеры обрабатывают однотипные запросы вручную",
            "LLM автоматизируют извлечение параметров из текста",
            "Модуль работает на сайте 24/7 без выходных",
        ],
        "notes": "Классический подбор тура медленный. ИИ позволяет принять запрос в свободной форме и быстро сформировать турпакет из каталога турфирмы.",
    },
    {
        "title": "Цель и задачи",
        "body": [
            "Цель: разработать и внедрить систему генерации турпакета на основе ИИ",
            "Анализ деятельности туроператора и процесса подбора туров",
            "Сравнительный анализ аналогов и выбор технологий",
            "Проектирование архитектуры модуля и структуры БД",
            "Реализация парсера, бэкенда FastAPI и фронтенда Vue.js",
            "Интеграция LLM, тестирование и экономическое обоснование",
        ],
        "numbered": True,
        "notes": "Цель — одним предложением. Задачи — по введению диплома.",
    },
    {
        "title": "Сравнение аналогов",
        "body": [
            "Travelpayouts, Tutu.ru, Яндекс.Путешествия — только формы",
            "CRM (1С: Турагентство) — учёт, но без ИИ и диалога",
            "Готовые чат-боты — чужой каталог, нет привязки к «Бон Вояж»",
            "Ни один аналог не сочетает все три функции сразу",
        ],
        "detail": [
            "КРИТЕРИИ СРАВНЕНИЯ",
            "· Ввод запроса (форма / свободный текст)",
            "· Диалог для уточнения параметров",
            "· Работа с каталогом конкретной турфирмы",
            "",
            "ПОИСКОВИКИ",
            "· Большая база, актуальные цены",
            "· Нет NLP и диалога",
            "",
            "НАШ МОДУЛЬ",
            "· NLP + диалог + свой каталог",
            "· Интеграция в bon-voyage28.ru",
        ],
        "notes": "Обоснование собственной разработки: нужны естественный язык, уточняющие вопросы и данные именно «Бон Вояж».",
    },
    {
        "title": "Объект и предмет исследования",
        "body": [
            "Объект: процесс подбора туристических пакетов в деятельности туроператора",
            "Предмет: методы сбора данных и обработки с LLM для генерации турпакетов",
            "Практическая база: ООО «Бон Вояж», г. Благовещенск",
            "Результат: модуль «AI Тур-Генератор» для сайта Планета 360",
        ],
        "notes": "Объект — процесс, предмет — методы и алгоритмы с применением больших языковых моделей.",
    },
    {
        "title": "Средства разработки",
        "body": [
            "Python 3.11, FastAPI, Uvicorn — серверная часть",
            "Vue.js 3 — клиентский интерфейс (чат)",
            "MySQL 8.0 — хранение каталога и сессий",
            "DeepSeek API + GigaChat — языковые модели",
            "BeautifulSoup + requests — парсинг bon-voyage28.ru",
            "Travelpayouts / Amadeus — данные о перелётах",
        ],
        "notes": "Клиент-серверная архитектура. Связка двух LLM даёт отказоустойчивость и соответствие 152-ФЗ (GigaChat).",
    },
    {
        "title": "База данных MySQL",
        "image": DB_SCHEMA,
        "body": [
            "7 таблиц: hotels, flights, user_sessions, user_queries, generated_tours, agency_leads, daily_stats",
        ],
        "notes": "ER-диаграмма из диплома. hotels — каталог туров (парсер), user_sessions — состояние диалога в JSON, generated_tours — готовые турпакеты.",
    },
    {
        "title": "Интерфейс (фронтенд)",
        "body": [
            "Одностраничное приложение на Vue.js (frontend/index.html)",
            "Чат: свободный ввод запроса на русском языке",
            "Выбор нейросети: Auto / GigaChat / DeepSeek",
            "Карточка тура: отель, перелёт, цена, рекомендация",
            "Кнопки «Купить самостоятельно» и «Обратиться в турфирму»",
            "Форма заявки: имя, телефон, email → менеджеру",
        ],
        "notes": "Можно показать демо: http://localhost:8000. Пример запроса: «Хочу в Китай с 10 по 20 июля, бюджет 80 000 руб.»",
    },
    {
        "title": "Серверная часть (бэкенд)",
        "body": [
            "FastAPI — центральный компонент (backend/app.py)",
            "POST /api/chat — приём сообщений и генерация тура",
            "ai_service.py — диалог LLM и сбор параметров",
            "database.py — SQL-запросы к MySQL",
            "date_validation.py, dialog_hints.py — серверная валидация",
            "Fallback: GigaChat → DeepSeek при сбое провайдера",
        ],
        "detail": [
            "АЛГОРИТМ /api/chat",
            "1. Создание/загрузка сессии",
            "2. LLM извлекает направление, даты, бюджет",
            "3. Поиск тура в таблице hotels",
            "4. LLM формирует турпакет + перелёт",
            "5. Ответ клиенту в JSON",
            "",
            "Дополнительно:",
            "· POST /api/reset — сброс диалога",
            "· POST /api/lead — заявка менеджеру",
            "· GET /admin/stats — статистика",
        ],
        "notes": "Асинхронная обработка: сервер не блокируется на время ответа нейросети (2–10 сек).",
    },
    {
        "title": "Экономическое обоснование",
        "body": [
            "Затраты на разработку: 107 200 руб.",
            "Эксплуатация: 47 100 руб./год",
            "Эффект от внедрения: 664 200 руб./год",
            "Окупаемость: 3–4 месяца",
        ],
        "detail": [
            "РАЗРАБОТКА",
            "· 200 ч × 500 руб. = 100 000 руб.",
            "· Материалы = 7 720 руб.",
            "",
            "АЛЬТЕРНАТИВЫ",
            "· Доп. менеджер ≈ 420 000 руб./год",
            "· Готовый чат-бот ≈ 50–120 тыс./год",
            "",
            "ВЫВОД",
            "Собственный модуль дешевле",
            "и использует каталог «Бон Вояж»",
        ],
        "notes": "Цифры из главы 5 диплома. При ~20 обращениях в день модуль окупается за 3–4 месяца.",
    },
    {
        "title": "Заключение",
        "body": [
            "Разработан модуль «AI Тур-Генератор» для ООО «Бон Вояж»",
            "Реализованы диалог на русском, парсер каталога, двухфазный AI-агент",
            "Двухпровайдерная схема GigaChat + DeepSeek",
            "Цель достигнута, все задачи выполнены",
            "Модуль готов к внедрению на bon-voyage28.ru",
        ],
        "notes": "Практическая значимость: снижение нагрузки на менеджеров, круглосуточный приём заявок, ускорение подбора тура.",
    },
    {
        "kind": "end",
        "title": "Спасибо за внимание!",
        "body": [
            "Готов ответить на ваши вопросы",
            "Демонстрация: http://localhost:8000",
            "ООО «Бон Вояж»: +7 (4162) 317-771",
        ],
        "notes": "Спасибо. Готов ответить на вопросы и показать работу модуля.",
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


def _picture(sid, name, x, y, cx, cy, embed: str):
    return f"""<p:pic>
<p:nvPicPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>
<p:blipFill><a:blip r:embed="{embed}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>"""


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


def _decor(num: int, kind: str | None, layout: str) -> str:
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
    if layout == "two_col":
        parts += [
            _rect(15, "leftC", 480000, 1120000, 4800000, 5000000, LT, r=8000),
            _rect(16, "rightC", 5400000, 1120000, 6200000, 5000000, WH, r=8000),
            _rect(21, "rightB", 5400000, 1120000, 6200000, 5000000, line=BD, r=8000),
        ]
    elif layout == "image":
        parts += [
            _rect(15, "imgBg", 360000, 1080000, 11400000, 5150000, WH, r=8000),
            _rect(16, "imgBd", 360000, 1080000, 11400000, 5150000, line=BD, r=8000),
        ]
    else:
        parts += [
            _rect(15, "card", 480000, 1120000, 11000000, 5000000, LT, r=8000),
            _rect(16, "cardB", 480000, 1120000, 11000000, 5000000, line=BD, r=8000),
        ]
    return "\n".join(parts)


def _slide_xml(sl: dict, num: int, image_rid: str | None = None) -> str:
    kind = sl.get("kind")
    special = kind in ("title", "end")
    has_image = bool(sl.get("image")) and image_rid
    two_col = bool(sl.get("detail")) and not special and not has_image

    if has_image:
        layout = "image"
    elif two_col:
        layout = "two_col"
    else:
        layout = "single"

    t_color = WH if special else G
    b_color = WH if special else DK
    t_sz = 2600 if kind == "title" else (3000 if kind == "end" else 2400)
    b_sz = 1700 if special else 1620

    title_xml = _title(sl["title"], t_sz, t_color, "ctr" if special else "l")
    body_xml = _body_xml(sl, b_sz, b_color)

    bg = _grad_bg() if special else _white_bg()
    decor = _decor(num, kind, layout)
    shapes = [decor]

    if special:
        shapes.append(_text(2, "Title", 700000, 1850000, 10800000, 2200000, title_xml, "ctr"))
        shapes.append(_text(3, "Body", 1200000, 4200000, 9800000, 1900000, body_xml, "ctr"))
    elif has_image:
        shapes.append(_text(2, "Title", 560000, 1040000, 10500000, 380000, title_xml))
        shapes.append(_picture(22, "ER Diagram", 420000, 1180000, 11300000, 4900000, image_rid))
        if sl.get("body"):
            shapes.append(_text(3, "Caption", 560000, 6100000, 11000000, 200000,
                                _para(sl["body"][0], 1300, color=GR, align="ctr"), "ctr"))
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
        '<Default Extension="png" ContentType="image/png"/>',
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
            image_rid = None
            img_path = sl.get("image")
            if img_path:
                img_path = Path(img_path)
                if not img_path.exists():
                    raise FileNotFoundError(f"Изображение не найдено: {img_path}")
                media_name = f"image{i}.png"
                z.writestr(f"ppt/media/{media_name}", img_path.read_bytes())
                rels.append(
                    f'<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{media_name}"/>'
                )
                image_rid = "rId3"

            z.writestr(f"ppt/slides/slide{i}.xml", _slide_xml(sl, i, image_rid))
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", f'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{chr(10).join(rels)}</Relationships>')
            z.writestr(f"ppt/notesSlides/notesSlide{i}.xml", _notes(sl.get("notes", "")))
            z.writestr(f"ppt/notesSlides/_rels/notesSlide{i}.xml.rels", f'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster" Target="../notesMasters/notesMaster1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="../slides/slide{i}.xml"/></Relationships>')

        z.writestr("ppt/notesMasters/notesMaster1.xml", '<?xml version="1.0"?><p:notesMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld></p:notesMaster>')
        z.writestr("ppt/notesMasters/_rels/notesMaster1.xml.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>')


def main():
    if not DB_SCHEMA.exists():
        import draw_db_schema
        draw_db_schema.main()

    build(OUT)
    copy = DOCS / "Diploma_Defense.pptx"
    copy.write_bytes(OUT.read_bytes())
    downloads = Path.home() / "Downloads" / "Тымченко_защита_презентация.pptx"
    downloads.write_bytes(OUT.read_bytes())
    print(f"Готово: {OUT}")
    print(f"Копия:  {copy}")
    print(f"Копия:  {downloads}")
    print(f"Слайдов: {len(SLIDES)}")


if __name__ == "__main__":
    main()
