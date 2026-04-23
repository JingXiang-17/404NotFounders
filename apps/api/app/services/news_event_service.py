from __future__ import annotations

from typing import Any


class NewsEventService:
    def normalize_articles(self, articles: list[dict[str, Any]], *, category: str) -> list[dict[str, Any]]:
        normalized = []
        seen = set()
        for article in articles:
            title = (article.get("title") or "").strip()
            source = ((article.get("source") or {}).get("name") or article.get("source") or "").strip()
            url = (article.get("url") or "").strip()
            dedupe_key = (title.lower(), source.lower())
            if not title or not url or dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            normalized.append(
                {
                    "event_id": f"{category}:{len(normalized) + 1}",
                    "title": title,
                    "published_at": article.get("publishedAt"),
                    "source": source,
                    "url": url,
                    "category": category,
                    "relevance_score": 1,
                    "affected_dimension": category,
                    "notes": article.get("description") or "",
                }
            )
        return normalized

