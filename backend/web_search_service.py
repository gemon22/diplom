"""Поиск справочной информации в интернете для ответов ассистента."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from config import Config

logger = logging.getLogger(__name__)

# Когда пользователь спрашивает факты, а не указывает параметры тура
_INFO_KEYWORDS = (
    "виза",
    "безвиз",
    "документ",
    "паспорт",
    "погод",
    "температур",
    "климат",
    "сезон",
    "достопримеч",
    "что посмотрет",
    "куда сходить",
    "сколько лететь",
    "часов лететь",
    "время полета",
    "перелет сколько",
    "прививк",
    "страховк",
    "таможн",
    "валют",
    "часовой пояс",
    "разница во времени",
    "безопасн",
    "экскурс",
)

_EXPLICIT_SEARCH = (
    "найди в интернет",
    "поищи в интернет",
    "загугли",
    "погугли",
    "поищи в сети",
    "найди в сети",
)


def needs_web_search(message: str, collected: dict | None = None) -> bool:
    if not Config.WEB_SEARCH_ENABLED:
        return False
    text = (message or "").strip().lower()
    if len(text) < 4:
        return False
    if any(p in text for p in _EXPLICIT_SEARCH):
        return True
    if any(k in text for k in _INFO_KEYWORDS):
        return True
    # Вопрос о стране из диалога: «а какая погода там?»
    if collected and collected.get("destination"):
        if any(
            q in text
            for q in (
                "какая погода",
                "нужна виза",
                "нужен паспорт",
                "что взять",
                "что посмотреть",
                "сколько лететь",
            )
        ):
            return True
    return False


def build_search_query(message: str, collected: dict | None = None) -> str:
    text = re.sub(r"\s+", " ", (message or "").strip())
    for phrase in _EXPLICIT_SEARCH:
        text = text.replace(phrase, "").strip()
    dest = (collected or {}).get("destination") or ""
    parts = [text]
    if dest and dest.lower() not in text.lower():
        parts.append(str(dest))
    query = " ".join(p for p in parts if p)
    if not any(w in query.lower() for w in ("туризм", "виза", "погода", "тур")):
        query += " туризм Россия"
    return query[:220]


def _search_sync(query: str, max_results: int) -> list[dict[str, Any]]:
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            rows = list(
                ddgs.text(
                    query,
                    max_results=max_results,
                    region=Config.WEB_SEARCH_REGION,
                )
            )
        return [
            {
                "title": r.get("title") or "",
                "url": r.get("href") or r.get("link") or "",
                "snippet": r.get("body") or r.get("snippet") or "",
            }
            for r in rows
            if (r.get("title") or r.get("body"))
        ]
    except Exception as e:
        logger.warning("DuckDuckGo search failed: %s", e)
        return _search_fallback_sync(query, max_results)


def _search_fallback_sync(query: str, max_results: int) -> list[dict[str, Any]]:
    """Запасной вариант через HTML DuckDuckGo (httpx + BeautifulSoup)."""
    try:
        import httpx
        from bs4 import BeautifulSoup

        with httpx.Client(timeout=12.0, follow_redirects=True) as client:
            resp = client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query, "b": "", "kl": Config.WEB_SEARCH_REGION},
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept-Language": "ru-RU,ru;q=0.9",
                },
            )
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        results: list[dict[str, Any]] = []
        for block in soup.select(".result"):
            title_el = block.select_one(".result__a")
            snippet_el = block.select_one(".result__snippet")
            if not title_el:
                continue
            results.append(
                {
                    "title": title_el.get_text(strip=True),
                    "url": title_el.get("href") or "",
                    "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                }
            )
            if len(results) >= max_results:
                break
        return results
    except Exception as e:
        logger.warning("Web search fallback failed: %s", e)
        return []


async def search_web(query: str, max_results: int | None = None) -> list[dict[str, Any]]:
    limit = max_results or Config.WEB_SEARCH_MAX_RESULTS
    return await asyncio.to_thread(_search_sync, query, limit)


def format_web_context(results: list[dict[str, Any]], query: str) -> str:
    if not results:
        return ""
    lines = [f"Запрос в интернет: «{query}»", "Справка (не цены туров — только факты):"]
    for i, row in enumerate(results, 1):
        title = (row.get("title") or "").strip()
        snippet = (row.get("snippet") or "").strip()
        url = (row.get("url") or "").strip()
        chunk = f"{i}. {title}"
        if snippet:
            chunk += f" — {snippet[:280]}"
        if url:
            chunk += f" ({url})"
        lines.append(chunk)
    return "\n".join(lines)


async def fetch_web_context(
    message: str, collected: dict | None = None
) -> tuple[str, str | None]:
    """
    Возвращает (текст для промпта, поисковый запрос или None).
    """
    if not needs_web_search(message, collected):
        return "", None
    query = build_search_query(message, collected)
    results = await search_web(query)
    if not results:
        return "", query
    return format_web_context(results, query), query
