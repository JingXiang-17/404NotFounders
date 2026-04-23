from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.core.settings import AppSettings
from app.providers.holiday_provider import HolidayWindow
from app.repositories.snapshot_repository import SnapshotRepository
from app.services.holiday_service import HolidayService
from app.services.market_data_service import MarketDataService
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


class FakeMarketProvider:
    def fetch_history(self, ticker: str) -> list[dict]:
        return [
            {"date": "2026-04-22", "open": 4.2, "high": 4.3, "low": 4.1, "close": 4.25, "volume": 10.0},
            {"date": "2026-04-23", "open": 4.25, "high": 4.35, "low": 4.2, "close": 4.3, "volume": 11.0},
        ]


class FailingMarketProvider:
    def fetch_history(self, ticker: str) -> list[dict]:
        raise RuntimeError("provider down")


class FakeHolidayProvider:
    def build_country_window(self, country_code: str, *, start_date, days: int) -> list[HolidayWindow]:
        return [
            HolidayWindow(
                country_code=country_code,
                date="2026-04-23",
                holiday_name="Demo Holiday",
                is_holiday=True,
                is_long_weekend=False,
                days_until_next_holiday=0,
            )
        ]


class MarketAndHolidayServiceTests(unittest.TestCase):
    def test_market_service_writes_snapshot(self) -> None:
        with workspace_temp_dir() as root:
            settings = build_settings(root)
            service = MarketDataService(FakeMarketProvider(), SnapshotRepository(settings))
            result = service.ingest_fx({"USDMYR": "dummy"})
            self.assertEqual(result["status"], "success")

    def test_market_service_keeps_last_known_good(self) -> None:
        with workspace_temp_dir() as root:
            settings = build_settings(root)
            repository = SnapshotRepository(settings)
            ok_service = MarketDataService(FakeMarketProvider(), repository)
            ok_service.ingest_energy({"BZ=F": "dummy"})
            failed_service = MarketDataService(FailingMarketProvider(), repository)
            result = failed_service.ingest_energy({"BZ=F": "dummy"})
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["fallback_snapshot_path"], "energy/latest.json")

    def test_holiday_service_writes_snapshot(self) -> None:
        with workspace_temp_dir() as root:
            settings = build_settings(root)
            service = HolidayService(FakeHolidayProvider(), SnapshotRepository(settings))
            result = service.ingest_holidays(("MY",), window_days=1)
            self.assertEqual(result["status"], "success")
