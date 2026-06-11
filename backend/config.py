import os
from pathlib import Path

from dotenv import load_dotenv

# .env в корне проекта
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Config:
    # DeepSeek
    DEEPSEEK_API_KEY = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
    # Официальный endpoint: https://api.deepseek.com/chat/completions
    DEEPSEEK_API_URL = os.getenv(
        "DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions"
    ).strip()
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()

    # GigaChat (Сбер) — https://developers.sber.ru/gigachat/
    GIGACHAT_CREDENTIALS = (os.getenv("GIGACHAT_CREDENTIALS") or "").strip()
    GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS").strip()
    GIGACHAT_AUTH_URL = os.getenv(
        "GIGACHAT_AUTH_URL",
        "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
    ).strip()
    GIGACHAT_API_URL = os.getenv(
        "GIGACHAT_API_URL",
        "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
    ).strip()
    GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat").strip()
    # На Windows часто нужно false до установки сертификатов НУЦ Минцифры
    GIGACHAT_VERIFY_SSL = os.getenv("GIGACHAT_VERIFY_SSL", "false").lower() in (
        "1",
        "true",
        "yes",
    )

    # Какой ИИ использовать: deepseek | gigachat | auto
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").strip().lower()
    # При auto — сначала этот (gigachat удобнее в РФ)
    LLM_PRIMARY = os.getenv("LLM_PRIMARY", "gigachat").strip().lower()
    LLM_FALLBACK = os.getenv("LLM_FALLBACK", "true").lower() in ("1", "true", "yes")

    # HTTP (Timeweb App Platform / Docker)
    PORT = int(os.getenv("PORT", "8000"))

    # MySQL
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "tour_generator")
    # Облачная MySQL Timeweb: БД создаётся в панели, CREATE DATABASE не нужен
    DB_SKIP_CREATE = os.getenv("DB_SKIP_CREATE", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    # Путь к CA-сертификату Timeweb Cloud (вкладка «Подключение» у БД)
    DB_SSL_CA = (os.getenv("DB_SSL_CA") or "").strip() or None
    DB_SSL_DISABLED = os.getenv("DB_SSL_DISABLED", "false").lower() in (
        "1",
        "true",
        "yes",
    )

    # При первом запуске в облаке — загрузить демо-данные (30 записей)
    SEED_DEMO_ON_START = os.getenv("SEED_DEMO_ON_START", "false").lower() in (
        "1",
        "true",
        "yes",
    )

    # Сайты для парсинга
    SITE_PRIMARY_URL = os.getenv("SITE_PRIMARY_URL", "https://bon-voyage28.ru/")
    SITE_SECONDARY_URL = os.getenv("SITE_SECONDARY_URL", "https://bonvoyage28.ru/")

    # Курс для фильтрации (бюджет пользователя в USD → рубли в БД)
    USD_TO_RUB = float(os.getenv("USD_TO_RUB", "95"))

    PARSE_INTERVAL_HOURS = int(os.getenv("PARSE_INTERVAL_HOURS", "12"))
    HISTORY_RETENTION_DAYS = int(os.getenv("HISTORY_RETENTION_DAYS", "7"))

    # Ссылки для кнопок в турпакете
    AGENCY_CONTACT_URL = os.getenv(
        "AGENCY_CONTACT_URL", "https://bon-voyage28.ru/"
    )

    # Travelpayouts / Aviasales Data API (авиабилеты)
    TRAVELPAYOUTS_TOKEN = (os.getenv("TRAVELPAYOUTS_TOKEN") or "").strip()
    TRAVELPAYOUTS_API_URL = os.getenv(
        "TRAVELPAYOUTS_API_URL", "https://api.travelpayouts.com"
    ).strip()
    # Город вылета по умолчанию (IATA). Благовещенск: BQS
    FLIGHTS_DEFAULT_ORIGIN = os.getenv("FLIGHTS_DEFAULT_ORIGIN", "BQS").strip().upper()
    # Какой источник авиабилетов использовать по умолчанию: travelpayouts | amadeus | all
    FLIGHTS_PROVIDER = os.getenv("FLIGHTS_PROVIDER", "all").strip().lower()

    # Amadeus Self-Service API
    AMADEUS_API_KEY = (os.getenv("AMADEUS_API_KEY") or "").strip()
    AMADEUS_API_SECRET = (os.getenv("AMADEUS_API_SECRET") or "").strip()
    # test.api.amadeus.com для теста, api.amadeus.com для прод
    AMADEUS_API_URL = os.getenv("AMADEUS_API_URL", "https://test.api.amadeus.com").strip()
