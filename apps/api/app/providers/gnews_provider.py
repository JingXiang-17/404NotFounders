from __future__ import annotations

from urllib.parse import urlencode
from urllib.request import urlopen
import json

from app.core.exceptions import ProviderError


class GNewsProvider:
    BASE_URL = "https://gnews.io/api/v4/search"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def fetch_articles(self, query: str, *, language: str = "en", max_results: int = 10) -> list[dict]:
        params = urlencode({"q": query, "lang": language, "max": max_results, "token": self.api_key})
        try:
            with urlopen(f"{self.BASE_URL}?{params}") as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - network-facing guard
            raise ProviderError(f"GNews request failed: {exc}") from exc
        return payload.get("articles", [])

