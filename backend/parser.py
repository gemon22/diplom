import logging
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import Config
from database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ограничения вежливого обхода
MAX_PAGES = 80
REQUEST_DELAY_SEC = 0.4
REQUEST_TIMEOUT = 30

SKIP_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".pdf",
    ".zip",
    ".doc",
    ".css",
    ".js",
)

SKIP_PATH_PARTS = (
    "/politika",
    "/wp-admin",
    "/wp-content",
    "/feed",
    "/cart",
    "/login",
)


class Parser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (compatible; TourGeneratorBot/1.0; +diploma-project)"
                ),
                "Accept-Language": "ru-RU,ru;q=0.9",
            }
        )

    def _base_host(self) -> str:
        return urlparse(Config.SITE_PRIMARY_URL).netloc.lower()

    def _is_same_site(self, url: str) -> bool:
        try:
            return urlparse(url).netloc.lower() in ("", self._base_host())
        except Exception:
            return False

    def _normalize_url(self, url: str, base: str) -> str | None:
        if not url or url.startswith(("#", "mailto:", "tel:", "javascript:")):
            return None
        full = urljoin(base, url)
        parsed = urlparse(full)
        if parsed.scheme not in ("http", "https"):
            return None
        if not self._is_same_site(full):
            return None
        path = (parsed.path or "/").lower()
        if any(path.endswith(ext) for ext in SKIP_EXTENSIONS):
            return None
        if any(part in path for part in SKIP_PATH_PARTS):
            return None
        # Без query/fragment — меньше дублей
        clean = f"{parsed.scheme}://{parsed.netloc}{path}"
        if clean.endswith("/") and path != "/":
            clean = clean.rstrip("/")
        return clean

    def discover_page_urls(self) -> list[str]:
        """Собирает URL страниц: sitemap + обход ссылок с главной."""
        base = Config.SITE_PRIMARY_URL.rstrip("/")
        found: set[str] = {base, base + "/"}

        # Sitemap
        for sm in (f"{base}/sitemap.xml", f"{base}/sitemap_index.xml"):
            try:
                r = self.session.get(sm, timeout=REQUEST_TIMEOUT)
                if r.status_code == 200:
                    for loc in re.findall(r"<loc>\s*(.*?)\s*</loc>", r.text, re.I):
                        n = self._normalize_url(loc.strip(), base)
                        if n:
                            found.add(n)
                    logger.info(f"Sitemap {sm}: +{len(found)} URLs total")
            except Exception as e:
                logger.debug(f"No sitemap {sm}: {e}")

        # BFS с главной
        queue = [base, base + "/"]
        visited: set[str] = set()

        while queue and len(visited) < MAX_PAGES:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            found.add(url)

            try:
                time.sleep(REQUEST_DELAY_SEC)
                resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
                if resp.status_code != 200:
                    continue
                if "text/html" not in resp.headers.get("Content-Type", ""):
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    nxt = self._normalize_url(a["href"], url)
                    if nxt and nxt not in visited and nxt not in queue:
                        queue.append(nxt)
                        found.add(nxt)
            except Exception as e:
                logger.warning(f"Crawl skip {url}: {e}")

        urls = sorted(found)
        logger.info(f"Discovered {len(urls)} pages to parse")
        return urls[:MAX_PAGES]

    def _destination_from_link(self, link: str) -> str:
        link_l = (link or "").lower()
        mapping = [
            ("/china/", "Китай"),
            ("/russia/", "Россия"),
            ("/thailand/", "Таиланд"),
            ("/turkey/", "Турция"),
            ("/vietnam/", "Вьетнам"),
            ("/korea/", "Корея"),
            ("/japan/", "Япония"),
            ("/uae/", "ОАЭ"),
            ("/egypt/", "Египет"),
            ("/greece/", "Греция"),
            ("/spain/", "Испания"),
            ("/italy/", "Италия"),
            ("/cuba/", "Куба"),
            ("/india/", "Индия"),
            ("/maldives/", "Мальдивы"),
            ("хэйхэ", "Китай"),
            ("шанхай", "Китай"),
            ("хэминху", "Китай"),
            ("бэйдайхэ", "Китай"),
            ("дальянь", "Китай"),
            ("космодром", "Россия"),
        ]
        for key, dest in mapping:
            if key in link_l:
                return dest
        return "Неизвестно"

    def parse_cards_from_html(self, html: str, page_url: str) -> list[dict]:
        base = Config.SITE_PRIMARY_URL.rstrip("/")
        soup = BeautifulSoup(html, "html.parser")
        tours = []

        for card in soup.select(".ex__item"):
            try:
                title_elem = card.select_one(".ex-card__title a")
                if not title_elem:
                    continue

                full_title = title_elem.get_text(strip=True)
                link = title_elem.get("href", "")
                if link and not link.startswith("http"):
                    link = f"{base}/{link.lstrip('/')}"
                link = self._normalize_url(link, page_url) or link

                price_match = re.search(r"от\s*(\d+)", full_title.replace(" ", ""))
                if not price_match:
                    price_match = re.search(r"(\d{4,})", full_title.replace(" ", ""))
                price = int(price_match.group(1)) if price_match else 0

                img_elem = card.select_one(".ex-card__img")
                img_url = img_elem.get("src", "") if img_elem else ""

                tours.append(
                    {
                        "name": full_title,
                        "destination": self._destination_from_link(
                            link or full_title.lower()
                        ),
                        "price_per_night": 0,
                        "total_stay_price": price,
                        "amenities": img_url or "",
                        "rating": 0,
                        "source_url": link or page_url,
                        "source_site": "bon_voyage_ru",
                    }
                )
            except Exception as e:
                logger.warning(f"Card parse error on {page_url}: {e}")

        return tours

    def parse_page(self, url: str) -> list[dict]:
        try:
            time.sleep(REQUEST_DELAY_SEC)
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return self.parse_cards_from_html(resp.text, url)
        except Exception as e:
            logger.warning(f"Failed page {url}: {e}")
            return []

    def parse_all_site(self) -> list[dict]:
        """Обход всех страниц сайта и сбор уникальных туров."""
        urls = self.discover_page_urls()
        by_link: dict[str, dict] = {}

        for i, url in enumerate(urls, 1):
            logger.info(f"[{i}/{len(urls)}] {url}")
            for tour in self.parse_page(url):
                key = tour.get("source_url") or tour.get("name")
                if key and key not in by_link:
                    by_link[key] = tour

        tours = list(by_link.values())
        logger.info(f"Unique tours collected: {len(tours)}")
        return tours

    def parse_tourvisor_widgets(self):
        logger.info("Skipping tourvisor site (dynamic content)")
        return []

    def save_tours_to_db(self, tours):
        if not tours:
            logger.info("No tours to save")
            return
        database = get_db()
        database.clear_hotels()
        database.insert_hotels(tours)
        logger.info(f"Saved {len(tours)} tours to database")

    def run(self):
        logger.info("Starting full-site parsing...")
        tours = self.parse_all_site()
        if tours:
            self.save_tours_to_db(tours)
        else:
            logger.warning("No tours parsed, database not updated")
        logger.info(f"Parsing completed. Total tours: {len(tours)}")

    def parse_bon_voyage_site(self):
        """Совместимость со старым вызовом."""
        return self.parse_all_site()


if __name__ == "__main__":
    Parser().run()
