import logging

import httpx

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_PLACEHOLDER_KEYS = {"", "ваш_ключ", "sk-your-key-here", "your_api_key_here"}


class DeepSeekClient:
    name = "deepseek"

    def __init__(self):
        self.api_url = Config.DEEPSEEK_API_URL
        self.model = Config.DEEPSEEK_MODEL
        self._last_error = ""

    @property
    def last_error(self) -> str:
        return self._last_error

    @property
    def api_key(self):
        return Config.DEEPSEEK_API_KEY

    def _key_problem(self) -> str | None:
        key = self.api_key
        if not key or key.lower() in _PLACEHOLDER_KEYS:
            return "Не задан DEEPSEEK_API_KEY в .env (platform.deepseek.com)."
        if not key.startswith("sk-"):
            return "DEEPSEEK_API_KEY должен начинаться с sk-"
        return None

    async def chat(self, messages: list[dict]) -> str | None:
        self._last_error = ""
        key_err = self._key_problem()
        if key_err:
            self._last_error = key_err
            logger.error(key_err)
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 800,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url, json=payload, headers=headers
                )
                if response.status_code != 200:
                    if response.status_code == 402:
                        self._last_error = (
                            "На аккаунте DeepSeek нет средств. "
                            "https://platform.deepseek.com/"
                        )
                    elif response.status_code == 401:
                        self._last_error = "Неверный DEEPSEEK_API_KEY."
                    else:
                        self._last_error = (
                            f"DeepSeek HTTP {response.status_code}: {response.text[:400]}"
                        )
                    logger.error(self._last_error)
                    return None
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except httpx.ConnectError:
            self._last_error = "Нет доступа к api.deepseek.com (интернет, VPN, файрвол)."
            logger.error(self._last_error)
            return None
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"DeepSeek error: {e}")
            return None


deepseek = DeepSeekClient()
