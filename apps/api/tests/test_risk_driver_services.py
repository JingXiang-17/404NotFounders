from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from app.providers.gnews_provider import GNewsProvider
from app.providers.openweather_provider import OpenWeatherProvider
from app.repositories.snapshot_repository import SnapshotRepository
from app.services.macro_data_service import MacroDataService
from app.services.news_event_service import NewsEventService
from app.services.weather_risk_service import WeatherRiskService


class FakeOpenDOSMProvider:
    async def fetch_dataset(self, dataset_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        if dataset_id == "ipi":
            return [
                {"date": "2026-01-01", "series_type": "growth_yoy", "sector": "manufacturing", "index": "-1.2"},
                {"date": "2025-12-01", "series_type": "growth_yoy", "sector": "manufacturing", "index": "0.5"},
            ]
        return [
            {"date": "2026-01-01", "exports": "1000", "imports": "1250"},
            {"date": "2025-12-01", "exports": "900", "imports": "800"},
        ]


class FakeGNewsProvider(GNewsProvider):
    def fetch_bucket_a(self) -> list[dict[str, Any]]:
        return [
            {
                "title": "Asia port congestion hits polypropylene shipping",
                "description": "Freight disruption for PP resin cargo",
                "published_at": "2026-04-24",
                "source": {"name": "Example Logistics"},
                "url": "https://example.com/logistics",
                "_query": "polypropylene shipping disruption Asia",
            }
        ]

    def fetch_bucket_b(self) -> list[dict[str, Any]]:
        return [
            {
                "title": "Ringgit outlook watched as oil prices rise",
                "description": "USD MYR exposure matters for Malaysian importers",
                "published_at": "2026-04-24",
                "source": {"name": "Example Finance"},
                "url": "https://example.com/finance",
                "_query": "ringgit outlook Malaysia imports",
            }
        ]


class FakeOpenWeatherProvider(OpenWeatherProvider):
    def __init__(self) -> None:
        super().__init__(api_key="test-key")

    async def fetch_forecast(self, *, latitude: float, longitude: float) -> dict[str, Any]:
        return {
            "list": [
                {
                    "dt_txt": "2026-04-24 12:00:00",
                    "wind": {"speed": 13.0},
                    "rain": {"3h": 1.0},
                    "weather": [{"description": "heavy rain"}],
                }
            ]
        }


@pytest.mark.asyncio
async def test_macro_service_refreshes_ipi_and_trade_snapshots() -> None:
    snapshot_dir = _local_snapshot_dir()
    service = MacroDataService(FakeOpenDOSMProvider(), SnapshotRepository(snapshot_dir))

    try:
        ipi = await service.refresh_ipi_snapshot()
        trade = await service.refresh_trade_snapshot()

        assert ipi.dataset == "macro"
        assert ipi.data[0]["status"] == "DANGER"
        assert ipi.data[0]["risk_driver"] == "dead_stock"
        assert trade.dataset == "macro_trade"
        assert trade.data[0]["trade_balance"] == -250.0
        assert service.get_macro_context_for_ai()["trade"]["status"] == "DANGER"
    finally:
        shutil.rmtree(snapshot_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_news_service_normalizes_and_scores_articles() -> None:
    snapshot_dir = _local_snapshot_dir()
    service = NewsEventService(FakeGNewsProvider(), SnapshotRepository(snapshot_dir))

    try:
        envelope = await service.refresh_news_snapshot()

        assert envelope.dataset == "news"
        assert envelope.status == "success"
        assert envelope.record_count == 2
        assert envelope.data[0]["relevance_score"] > 0
        assert service.get_top_events_for_context(top_n=1)[0]["risk_hint"] in {
            "lead_time_or_freight_risk",
            "fx_or_energy_risk",
        }
    finally:
        shutil.rmtree(snapshot_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_weather_service_summarizes_port_risk() -> None:
    snapshot_dir = _local_snapshot_dir()
    service = WeatherRiskService(FakeOpenWeatherProvider(), SnapshotRepository(snapshot_dir))

    try:
        envelope = await service.refresh_weather_snapshot(
            ports=[
                {
                    "port_code": "MYPKG",
                    "port_name": "Port Klang",
                    "country_code": "MY",
                    "latitude": 3.0019,
                    "longitude": 101.3999,
                }
            ]
        )

        assert envelope.dataset == "weather"
        assert envelope.status == "success"
        assert envelope.data[0]["port_code"] == "MYPKG"
        assert envelope.data[0]["alert_present"] is True
    finally:
        shutil.rmtree(snapshot_dir, ignore_errors=True)


def _local_snapshot_dir() -> Path:
    path = Path("apps/api/tests/.tmp_snapshots") / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path
