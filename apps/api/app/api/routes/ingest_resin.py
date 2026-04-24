from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.exceptions import ProviderError, SnapshotWriteFailed
from app.schemas.common import SnapshotEnvelope
from app.services.resin_benchmark_service import build_default_resin_service

router = APIRouter(prefix="/ingest/resin", tags=["ingestion"])


@router.post("/sunsirs", response_model=SnapshotEnvelope)
async def ingest_sunsirs_resin() -> SnapshotEnvelope:
    service = build_default_resin_service()
    try:
        return service.refresh_sunsirs_snapshot()
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except SnapshotWriteFailed as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal error during resin ingestion: {exc}") from exc
