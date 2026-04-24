from __future__ import annotations

from fastapi import APIRouter

from app.core.constants import DEFAULT_FX_PAIR_TICKERS
from app.repositories.snapshot_repository import SnapshotRepository
from app.schemas.analysis import FxLatestPoint
from app.schemas.common import SnapshotEnvelope

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.get("/latest/fx", response_model=list[FxLatestPoint])
async def get_latest_fx_points() -> list[FxLatestPoint]:
    repository = SnapshotRepository()
    points: list[FxLatestPoint] = []
    for pair in DEFAULT_FX_PAIR_TICKERS:
        envelope = repository.read_latest(f"fx/{pair}")
        if envelope is None or not envelope.data:
            continue
        latest_record = envelope.data[-1]
        close = latest_record.get("close")
        if close is None:
            continue
        points.append(
            FxLatestPoint(
                pair=pair,
                close=float(close),
                as_of=envelope.as_of,
            )
        )
    return points


@router.get("/latest/macro", response_model=dict[str, SnapshotEnvelope | None])
async def get_latest_macro_context() -> dict[str, SnapshotEnvelope | None]:
    repository = SnapshotRepository()
    return {
        "ipi": repository.read_latest("macro"),
        "trade": repository.read_latest("macro_trade"),
    }


@router.get("/latest/news", response_model=SnapshotEnvelope | None)
async def get_latest_news_events() -> SnapshotEnvelope | None:
    return SnapshotRepository().read_latest("news")


@router.get("/latest/weather", response_model=SnapshotEnvelope | None)
async def get_latest_weather_risk() -> SnapshotEnvelope | None:
    return SnapshotRepository().read_latest("weather")


@router.get("/latest/resin", response_model=SnapshotEnvelope | None)
async def get_latest_resin_benchmark() -> SnapshotEnvelope | None:
    return SnapshotRepository().read_latest("resin")
