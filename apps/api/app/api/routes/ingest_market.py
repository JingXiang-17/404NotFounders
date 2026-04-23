from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.exceptions import ExternalFetchFailed, SnapshotWriteFailed
from app.schemas.market import SnapshotRefreshSummary
from app.services.market_data_service import refresh_energy_snapshot, refresh_fx_snapshot

router = APIRouter(prefix="/ingest/market", tags=["ingest-market"])


class FXRefreshRequest(BaseModel):
    pair: str


class EnergyRefreshRequest(BaseModel):
    symbol: str = "BZ=F"


@router.post("/fx", response_model=SnapshotRefreshSummary)
async def ingest_fx_snapshot(request: FXRefreshRequest) -> SnapshotRefreshSummary:
    try:
        envelope = await refresh_fx_snapshot(pair=request.pair)
        return SnapshotRefreshSummary(
            dataset=envelope.dataset,
            source=envelope.source,
            fetched_at=str(envelope.fetched_at),
            as_of=str(envelope.as_of) if envelope.as_of is not None else None,
            status=envelope.status,
            record_count=envelope.record_count,
        )
    except ExternalFetchFailed as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except SnapshotWriteFailed as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/energy", response_model=SnapshotRefreshSummary)
async def ingest_energy_snapshot(request: EnergyRefreshRequest) -> SnapshotRefreshSummary:
    try:
        envelope = await refresh_energy_snapshot(symbol=request.symbol)
        return SnapshotRefreshSummary(
            dataset=envelope.dataset,
            source=envelope.source,
            fetched_at=str(envelope.fetched_at),
            as_of=str(envelope.as_of) if envelope.as_of is not None else None,
            status=envelope.status,
            record_count=envelope.record_count,
        )
    except ExternalFetchFailed as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except SnapshotWriteFailed as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
