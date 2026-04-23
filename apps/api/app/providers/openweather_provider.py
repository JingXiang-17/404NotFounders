from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import urlopen

from app.core.exceptions import ProviderError


class OpenWeatherProvider:
    BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def fetch_forecast(self, *, latitude: float, longitude: float) -> dict:
        params = urlencode({"lat": latitude, "lon": longitude, "appid": self.api_key, "units": "metric"})
        url = f"{self.BASE_URL}?{params}"
        try:
            with urlopen(url) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - network-facing guard
            raise ProviderError(f"OpenWeatherMap request failed: {exc}") from exc

