from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.core.exceptions import ValidationError
from app.core.settings import AppSettings
from app.repositories.raw_repository import RawRepository
from app.repositories.reference_repository import ReferenceRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.scrapers.resin_extractor import TrafilaturaExtractor
from app.scrapers.resin_source_registry import ResinSourceRegistry
from app.services.resin_benchmark_service import ResinBenchmarkService
from tests.test_utils import workspace_temp_dir


def build_settings(root: Path) -> AppSettings:
    data_dir = root / "data"
    return AppSettings(
        root_dir=root,
        data_dir=data_dir,
        reference_dir=data_dir / "reference",
        snapshot_dir=data_dir / "snapshots",
        raw_dir=data_dir / "raw",
        tmp_dir=data_dir / "tmp",
    )


class FakeLLMProvider:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def extract_resin_benchmark_from_text(self, text: str, *, source_name: str, source_url: str) -> dict:
        return dict(self.payload)


class TestableResinBenchmarkService(ResinBenchmarkService):
    def __init__(self, html: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._html = html

    def _fetch_html(self, url: str) -> str:  # type: ignore[override]
        return self._html


class ResinPipelineTests(unittest.TestCase):
    def test_resin_pipeline_saves_raw_artifacts_and_snapshot(self) -> None:
        with workspace_temp_dir() as root:
            settings = build_settings(root)
            reference_dir = settings.reference_dir
            reference_dir.mkdir(parents=True)
            source_registry = [
                {
                    "source_name": "ChemAnalyst",
                    "url": "https://www.chemanalyst.com/Petro-Chemicals/polypropylene-pp-15",
                    "domain": "chemanalyst.com",
                    "expected_region": "Asia",
                    "expected_content_type": "market-commentary",
                    "language": "en",
                    "priority": 1,
                    "notes": "Curated starting point for PP market commentary.",
                    "enabled": True,
                }
            ]
            (reference_dir / "source_registry.json").write_text(json.dumps(source_registry), encoding="utf-8")
            repository = ReferenceRepository(settings)
            service = TestableResinBenchmarkService(
                html="<html><body>Asia PP benchmark at USD 1140/MT on 2026-04-23.</body></html>",
                source_registry=ResinSourceRegistry(repository),
                raw_repository=RawRepository(settings),
                snapshot_repository=SnapshotRepository(settings),
                extractor=TrafilaturaExtractor(),
                llm_provider=FakeLLMProvider(
                    {
                        "commodity": "PP Resin",
                        "region": "Asia",
                        "price_value": 1140.0,
                        "currency": "USD",
                        "unit": "USD/MT",
                        "date_reference": "2026-04-23",
                        "confidence": 0.91,
                        "evidence_snippet": "USD 1140/MT",
                        "source_name": "ChemAnalyst",
                        "source_url": "https://www.chemanalyst.com/Petro-Chemicals/polypropylene-pp-15",
                    }
                ),
            )
            result = service.ingest_resin_snapshot()
            self.assertEqual(result["status"], "success")
            self.assertTrue(Path(result["raw_html_path"]).exists())
            self.assertTrue(Path(result["raw_text_path"]).exists())

    def test_resin_pipeline_rejects_invalid_llm_parse(self) -> None:
        with workspace_temp_dir() as root:
            settings = build_settings(root)
            reference_dir = settings.reference_dir
            reference_dir.mkdir(parents=True)
            (reference_dir / "source_registry.json").write_text(
                json.dumps(
                    [
                        {
                            "source_name": "ChemAnalyst",
                            "url": "https://www.chemanalyst.com/Petro-Chemicals/polypropylene-pp-15",
                            "domain": "chemanalyst.com",
                            "expected_region": "Asia",
                            "expected_content_type": "market-commentary",
                            "language": "en",
                            "priority": 1,
                            "notes": "Curated starting point for PP market commentary.",
                            "enabled": True,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            service = TestableResinBenchmarkService(
                html="<html><body>No useful content.</body></html>",
                source_registry=ResinSourceRegistry(ReferenceRepository(settings)),
                raw_repository=RawRepository(settings),
                snapshot_repository=SnapshotRepository(settings),
                extractor=TrafilaturaExtractor(),
                llm_provider=FakeLLMProvider(
                    {
                        "commodity": "PP Resin",
                        "region": "Asia",
                        "price_value": 50.0,
                        "currency": "USD",
                        "unit": "USD/MT",
                        "date_reference": "2026-04-23",
                        "confidence": 0.2,
                        "evidence_snippet": "",
                        "source_name": "ChemAnalyst",
                        "source_url": "https://www.chemanalyst.com/Petro-Chemicals/polypropylene-pp-15",
                    }
                ),
            )
            with self.assertRaises(ValidationError):
                service.ingest_resin_snapshot()
