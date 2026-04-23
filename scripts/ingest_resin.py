from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.core.exceptions import IngestionError
from app.core.settings import AppSettings
from app.providers.llm_provider import NullLLMProvider
from app.repositories.raw_repository import RawRepository
from app.repositories.reference_repository import ReferenceRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.scrapers.resin_extractor import TrafilaturaExtractor
from app.scrapers.resin_source_registry import ResinSourceRegistry
from app.services.resin_benchmark_service import ResinBenchmarkService


def main() -> int:
    try:
        settings = AppSettings.from_env()
        service = ResinBenchmarkService(
            source_registry=ResinSourceRegistry(ReferenceRepository(settings)),
            raw_repository=RawRepository(settings),
            snapshot_repository=SnapshotRepository(settings),
            extractor=TrafilaturaExtractor(),
            llm_provider=NullLLMProvider(),
        )
        result = service.ingest_resin_snapshot()
        print(result)
        return 0
    except IngestionError as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
