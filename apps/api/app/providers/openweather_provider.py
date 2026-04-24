from __future__ import annotations

import httpx

from app.core.exceptions import ProviderError


class OpenWeatherProvider:
    BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def fetch_forecast(self, *, latitude: float, longitude: float) -> dict:
        """Async fetch of a 5-day/3-hour forecast for a given lat/lon."""
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            raise ProviderError(f"OpenWeatherMap request failed ({latitude},{longitude}): {exc}") from exc
