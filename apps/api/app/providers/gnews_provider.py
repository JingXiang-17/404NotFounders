from __future__ import annotations

import logging
from functools import cached_property
from typing import Any

from app.core.exceptions import ProviderError

logger = logging.getLogger(__name__)

BUCKET_A_QUERIES = [
    "polypropylene shipping disruption Asia",
    "petrochemical supply disruption Asia",
    "port congestion Asia plastics",
    "PP resin price Asia",
]

BUCKET_B_QUERIES = [
    "ringgit outlook Malaysia imports",
    "oil prices Asia plastics manufacturing",
    "USD MYR Malaysia manufacturing",
    "Malaysia polymer import tariff",
]


class GNewsProvider:
    """Wraps the gnews library, which reads Google News RSS without an API key."""

    def __init__(self, max_results: int = 5, language: str = "en", country: str = "MY") -> None:
        self.max_results = max_results
        self.language = language
        self.country = country

    @cached_property
    def client(self):  # type: ignore[return]
        try:
            from gnews import GNews  # type: ignore[import]
        except ImportError as exc:
            raise ProviderError("gnews library is not installed. Run: pip install gnews") from exc
        return GNews(
            language=self.language,
            country=self.country,
            max_results=self.max_results,
        )

    def fetch_articles(self, query: str) -> list[dict[str, Any]]:
        try:
            raw = self.client.get_news(query)
        except Exception as exc:
            raise ProviderError(f"GNews fetch failed for '{query}': {exc}") from exc

        results: list[dict[str, Any]] = []
        for item in raw or []:
            publisher = item.get("publisher") or {}
            source_name = publisher.get("title", "") if isinstance(publisher, dict) else str(publisher)
            results.append(
                {
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "published_at": item.get("published date", ""),
                    "source": {"name": source_name},
                    "url": item.get("url", ""),
                }
            )
        return results

    def fetch_bucket_a(self) -> list[dict[str, Any]]:
        return self._fetch_bucket(BUCKET_A_QUERIES, "logistics")

    def fetch_bucket_b(self) -> list[dict[str, Any]]:
        return self._fetch_bucket(BUCKET_B_QUERIES, "finance")

    def _fetch_bucket(self, queries: list[str], bucket_label: str) -> list[dict[str, Any]]:
        articles: list[dict[str, Any]] = []
        for query in queries:
            try:
                batch = self.fetch_articles(query)
            except ProviderError as exc:
                logger.warning("GNews bucket '%s' query failed: %s", query, exc)
                continue
            for article in batch:
                article["_query_bucket"] = bucket_label
                article["_query"] = query
            articles.extend(batch)
            logger.debug("GNews '%s' returned %d articles", query, len(batch))
        return articles
