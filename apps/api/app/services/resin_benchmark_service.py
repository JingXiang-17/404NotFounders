from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from app.core.exceptions import ProviderError
from app.repositories.raw_repository import RawRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.schemas.common import make_snapshot_envelope, validate_resin_record
from app.scrapers.resin_extractor import TrafilaturaExtractor
from app.scrapers.resin_source_registry import ResinSourceRegistry


class ResinBenchmarkService:
    def __init__(
        self,
        *,
        source_registry: ResinSourceRegistry,
        raw_repository: RawRepository,
        snapshot_repository: SnapshotRepository,
        extractor: TrafilaturaExtractor,
        llm_provider: Any,
    ) -> None:
        self.source_registry = source_registry
        self.raw_repository = raw_repository
        self.snapshot_repository = snapshot_repository
        self.extractor = extractor
        self.llm_provider = llm_provider

    def ingest_resin_snapshot(self) -> dict[str, Any]:
        source = self.source_registry.select_primary_source()
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        slug = self.source_registry.slugify(source["source_name"])
        html = self._fetch_html(source["url"])
        html_filename = f"{slug}_{fetched_at.replace(':', '').replace('-', '').replace('T', '_').replace('Z', 'Z')}.html"
        html_path = self.raw_repository.write_text("resin_html", html_filename, html)
        text = self.extractor.extract_text(html)
        text_filename = Path(html_filename).with_suffix(".txt").name
        text_path = self.raw_repository.write_text("resin_text", text_filename, text)
        record = self.llm_provider.extract_resin_benchmark_from_text(
            text,
            source_name=source["source_name"],
            source_url=source["url"],
        )
        validate_resin_record(record)
        envelope = make_snapshot_envelope(
            dataset="resin",
            source=source["source_name"],
            fetched_at=fetched_at,
            as_of=record["date_reference"],
            status="success",
            data=[record],
        )
        snapshot_path = self.snapshot_repository.write_snapshot("resin", envelope)
        return {
            "status": "success",
            "snapshot_path": str(snapshot_path),
            "raw_html_path": str(html_path),
            "raw_text_path": str(text_path),
            "record_count": 1,
            "fetched_at": fetched_at,
        }

    @staticmethod
    def _fetch_html(url: str) -> str:
        try:
            with urlopen(url) as response:
                return response.read().decode("utf-8", errors="ignore")
        except Exception as exc:  # pragma: no cover - network-facing guard
            raise ProviderError(f"Unable to fetch resin source HTML: {exc}") from exc

