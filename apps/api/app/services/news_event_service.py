from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from app.core.exceptions import ProviderError
from app.providers.gnews_provider import GNewsProvider
from app.repositories.snapshot_repository import SnapshotRepository
from app.schemas.common import SnapshotEnvelope, make_snapshot_envelope

logger = logging.getLogger(__name__)


class NewsEventService:
    def __init__(self, provider: GNewsProvider, snapshot_repository: SnapshotRepository) -> None:
        self.provider = provider
        self.snapshot_repository = snapshot_repository

    async def refresh_news_snapshot(self) -> SnapshotEnvelope:
        fetched_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        try:
            bucket_a, bucket_b = await asyncio.gather(
                asyncio.to_thread(self.provider.fetch_bucket_a),
                asyncio.to_thread(self.provider.fetch_bucket_b),
            )
        except ProviderError as exc:
            latest = self.snapshot_repository.read_latest("news")
            if latest is None:
                raise
            logger.warning("GNews failed, using latest snapshot: %s", exc)
            return self._partial_from_latest(latest)

        records = self.normalize_articles(bucket_a, category="logistics")
        records.extend(self.normalize_articles(bucket_b, category="finance"))
        records.sort(key=lambda row: row["relevance_score"], reverse=True)

        envelope = SnapshotEnvelope(
            **make_snapshot_envelope(
                dataset="news",
                source="gnews",
                fetched_at=fetched_at,
                as_of=fetched_at[:10],
                status="success" if records else "partial",
                data=records,
            )
        )
        self.snapshot_repository.write_snapshot("news", envelope)
        logger.info("News snapshot written: %d records", len(records))
        return envelope

    def normalize_articles(self, articles: list[dict[str, Any]], *, category: str) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        high_relevance_keywords = {
            "polypropylene",
            "pp resin",
            "petrochemical",
            "polymer",
            "freight",
            "shipping",
            "port",
            "congestion",
            "ringgit",
            "myr",
            "plastics",
            "tariff",
            "import",
            "manufacturing",
        }

        for article in articles:
            title = (article.get("title") or "").strip()
            source_obj = article.get("source") or {}
            source = source_obj.get("name") if isinstance(source_obj, dict) else str(source_obj)
            source = source.strip()
            url = (article.get("url") or "").strip()
            dedupe_key = (title.lower(), source.lower())
            if not title or not url or dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            combined_text = f"{title} {article.get('description') or ''}".lower()
            keyword_hits = sum(1 for keyword in high_relevance_keywords if keyword in combined_text)
            relevance_score = round(min(1.0, keyword_hits / 3), 2)
            normalized.append(
                {
                    "event_id": f"{category}:{len(normalized) + 1}",
                    "title": title,
                    "published_at": article.get("published_at") or article.get("publishedAt", ""),
                    "source": source,
                    "url": url,
                    "category": category,
                    "relevance_score": relevance_score,
                    "affected_dimension": category,
                    "notes": (article.get("description") or "")[:300],
                    "query": article.get("_query", ""),
                    "risk_hint": self._risk_hint(category, combined_text),
                }
            )
        return sorted(normalized, key=lambda row: row["relevance_score"], reverse=True)

    def get_top_events_for_context(self, top_n: int = 5) -> list[dict[str, Any]]:
        snapshot = self.snapshot_repository.read_latest("news")
        if snapshot is None:
            return []
        records = snapshot.data or []
        return sorted(records, key=lambda row: row.get("relevance_score", 0), reverse=True)[:top_n]

    @staticmethod
    def _risk_hint(category: str, text: str) -> str:
        if category == "logistics" and any(term in text for term in ("congestion", "disruption", "freight")):
            return "lead_time_or_freight_risk"
        if category == "finance" and any(term in text for term in ("ringgit", "usd", "myr", "oil")):
            return "fx_or_energy_risk"
        return category

    @staticmethod
    def _partial_from_latest(latest: SnapshotEnvelope) -> SnapshotEnvelope:
        return SnapshotEnvelope(
            dataset=latest.dataset,
            source=latest.source,
            fetched_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            as_of=latest.as_of,
            status="partial",
            record_count=latest.record_count,
            data=latest.data,
        )


def build_default_news_service() -> NewsEventService:
    return NewsEventService(GNewsProvider(max_results=5), SnapshotRepository())
