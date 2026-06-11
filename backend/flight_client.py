import logging
from datetime import datetime

import httpx

from config import Config

logger = logging.getLogger(__name__)


DEST_IATA = {
    "китай": "BJS",
    "россия": "MOW",
    "таиланд": "BKK",
    "турция": "IST",
    "вьетнам": "SGN",
    "оаэ": "DXB",
    "япония": "TYO",
}


class _BaseClient:
    name = "base"

    def __init__(self):
        self.last_error = ""

    def _resolve_destination_iata(self, value: str | None) -> str | None:
        if not value:
            return None
        v = value.strip()
        if len(v) == 3 and v.isalpha():
            return v.upper()
        return DEST_IATA.get(v.lower())


class TravelpayoutsClient(_BaseClient):
    name = "travelpayouts"

    def __init__(self):
        super().__init__()
        self.base_url = Config.TRAVELPAYOUTS_API_URL.rstrip("/")
        self.token = Config.TRAVELPAYOUTS_TOKEN

    async def search_flights(
        self, destination: str, date_from: str, date_to: str, origin_iata: str | None, currency: str
    ) -> list[dict]:
        self.last_error = ""
        if not self.token:
            self.last_error = "TRAVELPAYOUTS_TOKEN не задан"
            return []
        dst = self._resolve_destination_iata(destination)
        if not dst:
            self.last_error = f"Не удалось сопоставить направление '{destination}' с IATA."
            return []
        origin = (origin_iata or Config.FLIGHTS_DEFAULT_ORIGIN or "BQS").upper()
        month = date_from[:7] if len(date_from) >= 7 else datetime.now().strftime("%Y-%m")
        params = {
            "origin": origin,
            "destination": dst,
            "depart_date": month,
            "return_date": date_to,
            "currency": currency.lower(),
            "token": self.token,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(f"{self.base_url}/v1/prices/cheap", params=params)
                if resp.status_code != 200:
                    self.last_error = f"HTTP {resp.status_code}: {resp.text[:250]}"
                    return []
                payload = resp.json()
        except Exception as e:
            self.last_error = str(e)
            return []
        data = payload.get("data") or {}
        bucket = data.get(dst)
        if isinstance(bucket, dict):
            entries = (
                list(bucket.values())
                if any(isinstance(v, dict) for v in bucket.values())
                else [bucket]
            )
        else:
            entries = []
        offers = []
        for item in entries:
            if isinstance(item, dict):
                offers.append(
                    {
                        "origin": origin,
                        "destination": dst,
                        "price": float(item.get("price") or 0),
                        "airline": item.get("airline") or "",
                        "departure_at": item.get("departure_at"),
                        "return_at": item.get("return_at"),
                        "link": item.get("link") or "",
                        "source_site": self.name,
                        "currency": currency.upper(),
                    }
                )
        return offers


class AmadeusClient(_BaseClient):
    name = "amadeus"

    def __init__(self):
        super().__init__()
        self.client_id = (Config.AMADEUS_API_KEY or "").strip()
        self.client_secret = (Config.AMADEUS_API_SECRET or "").strip()
        self.base_url = Config.AMADEUS_API_URL.rstrip("/")
        self._access_token = ""

    async def _get_token(self) -> str:
        if self._access_token:
            return self._access_token
        if not self.client_id or not self.client_secret:
            self.last_error = "AMADEUS_API_KEY/AMADEUS_API_SECRET не заданы"
            return ""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/v1/security/oauth2/token",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                )
                if resp.status_code != 200:
                    self.last_error = f"Amadeus auth HTTP {resp.status_code}: {resp.text[:250]}"
                    return ""
                self._access_token = resp.json().get("access_token", "")
                return self._access_token
        except Exception as e:
            self.last_error = str(e)
            return ""

    async def search_flights(
        self, destination: str, date_from: str, date_to: str, origin_iata: str | None, currency: str
    ) -> list[dict]:
        self.last_error = ""
        token = await self._get_token()
        if not token:
            return []
        dst = self._resolve_destination_iata(destination)
        if not dst:
            self.last_error = f"Не удалось сопоставить направление '{destination}' с IATA."
            return []
        origin = (origin_iata or Config.FLIGHTS_DEFAULT_ORIGIN or "BQS").upper()
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": dst,
            "departureDate": date_from,
            "returnDate": date_to,
            "adults": 1,
            "max": 20,
            "currencyCode": currency.upper(),
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.base_url}/v2/shopping/flight-offers",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
                if resp.status_code != 200:
                    self.last_error = f"Amadeus HTTP {resp.status_code}: {resp.text[:250]}"
                    return []
                payload = resp.json()
        except Exception as e:
            self.last_error = str(e)
            return []

        offers = []
        for item in payload.get("data", []):
            try:
                itineraries = item.get("itineraries") or []
                dep_at = (
                    itineraries[0]["segments"][0]["departure"]["at"] if itineraries else None
                )
                ret_at = (
                    itineraries[1]["segments"][0]["departure"]["at"]
                    if len(itineraries) > 1
                    else None
                )
                validating = item.get("validatingAirlineCodes") or []
                airline = validating[0] if validating else ""
                price_total = float((item.get("price") or {}).get("total") or 0)
                offers.append(
                    {
                        "origin": origin,
                        "destination": dst,
                        "price": price_total,
                        "airline": airline,
                        "departure_at": dep_at,
                        "return_at": ret_at,
                        "link": "",
                        "source_site": self.name,
                        "currency": currency.upper(),
                    }
                )
            except Exception:
                continue
        return offers


class FlightsClient:
    """Агрегатор авиабилетов: travelpayouts / amadeus / all."""

    name = "flights-multi"

    def __init__(self):
        self.last_error = ""
        self.tp = TravelpayoutsClient()
        self.amadeus = AmadeusClient()

    async def search_flights(
        self,
        destination: str,
        date_from: str,
        date_to: str,
        origin_iata: str | None = None,
        currency: str = "rub",
        provider: str | None = None,
    ) -> list[dict]:
        mode = (provider or Config.FLIGHTS_PROVIDER or "all").lower().strip()
        clients = []
        if mode == "travelpayouts":
            clients = [self.tp]
        elif mode == "amadeus":
            clients = [self.amadeus]
        else:
            clients = [self.tp, self.amadeus]

        errors = []
        all_offers = []
        for client in clients:
            items = await client.search_flights(
                destination=destination,
                date_from=date_from,
                date_to=date_to,
                origin_iata=origin_iata,
                currency=currency,
            )
            if items:
                all_offers.extend(items)
            elif client.last_error:
                errors.append(f"{client.name}: {client.last_error}")

        # дедуп приблизительно по ключу
        uniq = {}
        for o in all_offers:
            key = (
                o.get("source_site"),
                o.get("airline"),
                o.get("departure_at"),
                o.get("return_at"),
                round(float(o.get("price") or 0), 2),
            )
            if key not in uniq:
                uniq[key] = o

        result = list(uniq.values())
        result.sort(key=lambda x: float(x.get("price") or 0))
        self.last_error = "; ".join(errors) if errors and not result else ""
        return result


flights_client = FlightsClient()
