from pathlib import Path
import asyncio

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import app.services.market_data_service as market_data_service
from app.main import app
from app.providers.yfinance_provider import _normalize_history_frame
from app.schemas.common import SnapshotEnvelope


def _fixture_frame() -> pd.DataFrame:
    fixture_path = Path(__file__).parent / "fixtures" / "market_history.csv"
    frame = pd.read_csv(fixture_path)
    return frame[["date", "open", "high", "low", "close"]]


def test_normalize_history_frame_handles_multiindex_columns():
    index = pd.to_datetime(["2026-04-20", "2026-04-21"])
    frame = pd.DataFrame(
        {
            ("Open", "MYR=X"): [4.72, 4.73],
            ("High", "MYR=X"): [4.74, 4.75],
            ("Low", "MYR=X"): [4.71, 4.72],
            ("Close", "MYR=X"): [4.73, 4.74],
        },
        index=index,
    )
    frame.index.name = "Date"

    normalized = _normalize_history_frame(frame)

    assert list(normalized.columns) == ["date", "open", "high", "low", "close"]
    assert normalized.iloc[0].to_dict() == {
        "date": "2026-04-20",
        "open": 4.72,
        "high": 4.74,
        "low": 4.71,
        "close": 4.73,
    }


def test_refresh_fx_snapshot_writes_envelope(monkeypatch):
    fixture_frame = _fixture_frame()
    written_snapshots: dict[str, SnapshotEnvelope] = {}

    async def fake_fetch_fx_history(pair: str, period: str = "1y") -> pd.DataFrame:
        assert pair == "USDMYR"
        assert period == "1y"
        return fixture_frame

    class FakeSnapshotRepository:
        def write_snapshot(self, dataset: str, envelope: SnapshotEnvelope) -> None:
            written_snapshots[dataset] = envelope

    monkeypatch.setattr(market_data_service, "fetch_fx_history", fake_fetch_fx_history)
    monkeypatch.setattr(market_data_service, "SnapshotRepository", FakeSnapshotRepository)

    envelope = asyncio.run(market_data_service.refresh_fx_snapshot("USDMYR"))

    assert envelope.dataset == "fx/USDMYR"
    assert envelope.source == "yfinance"
    assert envelope.status == "success"
    assert envelope.record_count == 3
    assert envelope.data[0]["pair"] == "USDMYR"
    assert written_snapshots["fx/USDMYR"].record_count == 3


def test_refresh_energy_snapshot_writes_envelope(monkeypatch):
    fixture_frame = _fixture_frame()
    written_snapshots: dict[str, SnapshotEnvelope] = {}

    async def fake_fetch_energy_history(symbol: str, period: str = "1y") -> pd.DataFrame:
        assert symbol == "BZ=F"
        assert period == "1y"
        return fixture_frame

    class FakeSnapshotRepository:
        def write_snapshot(self, dataset: str, envelope: SnapshotEnvelope) -> None:
            written_snapshots[dataset] = envelope

    monkeypatch.setattr(market_data_service, "fetch_energy_history", fake_fetch_energy_history)
    monkeypatch.setattr(market_data_service, "SnapshotRepository", FakeSnapshotRepository)

    envelope = asyncio.run(market_data_service.refresh_energy_snapshot("BZ=F"))

    assert envelope.dataset == "energy/BZ=F"
    assert envelope.record_count == 3
    assert envelope.data[0]["series_name"] == "Brent Crude"
    assert written_snapshots["energy/BZ=F"].record_count == 3


def test_ingest_market_fx_route(monkeypatch):
    fixture_frame = _fixture_frame()

    async def fake_refresh_fx_snapshot(pair: str) -> SnapshotEnvelope:
        assert pair == "USDMYR"
        return SnapshotEnvelope(
            dataset="fx/USDMYR",
            source="yfinance",
            fetched_at="2026-04-23T10:00:00Z",
            as_of="2026-04-22T00:00:00Z",
            status="success",
            record_count=len(fixture_frame),
            data=[],
        )

    monkeypatch.setattr("app.api.routes.ingest_market.refresh_fx_snapshot", fake_refresh_fx_snapshot)

    client = TestClient(app)
    response = client.post("/ingest/market/fx", json={"pair": "USDMYR"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset"] == "fx/USDMYR"
    assert payload["record_count"] == 3
    assert payload["status"] == "success"
    assert "data" not in payload
