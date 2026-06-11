import logging
import time
import uuid

import httpx

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GigaChatClient:
    """Клиент GigaChat API (Сбер). https://developers.sber.ru/docs/ru/gigachat/"""

    name = "gigachat"

    def __init__(self):
        self._access_token: str | None = None
        self._token_expires_at: float = 0
        self._last_error = ""

    @property
    def last_error(self) -> str:
        return self._last_error

    def _credentials_problem(self) -> str | None:
        cred = Config.GIGACHAT_CREDENTIALS
        if not cred or cred.lower() in {"", "ваш_ключ", "your_credentials"}:
            return (
                "Не задан GIGACHAT_CREDENTIALS в .env "
                "(ключ авторизации из developers.sber.ru → GigaChat API)."
            )
        return None

    async def _fetch_token(self, client: httpx.AsyncClient) -> bool:
        cred_err = self._credentials_problem()
        if cred_err:
            self._last_error = cred_err
            return False

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
            "Authorization": f"Basic {Config.GIGACHAT_CREDENTIALS}",
        }
        data = {"scope": Config.GIGACHAT_SCOPE}

        try:
            response = await client.post(
                Config.GIGACHAT_AUTH_URL,
                headers=headers,
                data=data,
            )
            if response.status_code != 200:
                self._last_error = f"GigaChat OAuth HTTP {response.status_code}: {response.text[:300]}"
                logger.error(self._last_error)
                return False
            payload = response.json()
            self._access_token = payload.get("access_token")
            expires_at = payload.get("expires_at")
            if expires_at:
                # expires_at в миллисекундах
                self._token_expires_at = float(expires_at) / 1000.0 - 60
            else:
                self._token_expires_at = time.time() + 25 * 60
            return bool(self._access_token)
        except httpx.ConnectError:
            self._last_error = (
                "Нет соединения с GigaChat (ngw.devices.sberbank.ru). "
                "Проверьте интернет; при ошибке SSL установите GIGACHAT_VERIFY_SSL=false."
            )
            return False
        except Exception as e:
            self._last_error = f"GigaChat OAuth: {e}"
            logger.error(self._last_error)
            return False

    async def _ensure_token(self, client: httpx.AsyncClient) -> bool:
        if self._access_token and time.time() < self._token_expires_at:
            return True
        return await self._fetch_token(client)

    async def chat(self, messages: list[dict]) -> str | None:
        self._last_error = ""
        verify = Config.GIGACHAT_VERIFY_SSL

        try:
            async with httpx.AsyncClient(timeout=90.0, verify=verify) as client:
                if not await self._ensure_token(client):
                    return None

                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self._access_token}",
                }
                payload = {
                    "model": Config.GIGACHAT_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 800,
                    "stream": False,
                }
                response = await client.post(
                    Config.GIGACHAT_API_URL,
                    json=payload,
                    headers=headers,
                )
                if response.status_code == 401:
                    self._access_token = None
                    if await self._ensure_token(client):
                        headers["Authorization"] = f"Bearer {self._access_token}"
                        response = await client.post(
                            Config.GIGACHAT_API_URL,
                            json=payload,
                            headers=headers,
                        )

                if response.status_code != 200:
                    self._last_error = (
                        f"GigaChat HTTP {response.status_code}: {response.text[:400]}"
                    )
                    logger.error(self._last_error)
                    return None

                result = response.json()
                return result["choices"][0]["message"]["content"]
        except httpx.ConnectError:
            self._last_error = (
                "Нет соединения с gigachat.devices.sberbank.ru. "
                "Попробуйте GIGACHAT_VERIFY_SSL=false в .env."
            )
            logger.error(self._last_error)
            return None
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"GigaChat error: {e}")
            return None


gigachat = GigaChatClient()
