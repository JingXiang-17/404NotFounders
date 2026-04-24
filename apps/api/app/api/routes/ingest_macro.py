from fastapi import APIRouter, HTTPException

from app.core.exceptions import ProviderError
from app.services.macro_data_service import build_default_macro_service
from app.schemas.common import SnapshotEnvelope

router = APIRouter(prefix="/ingest/macro", tags=["ingestion"])


@router.post("", response_model=dict[str, SnapshotEnvelope])
async def ingest_macro_all() -> dict[str, SnapshotEnvelope]:
    service = build_default_macro_service()
    try:
        ipi = await service.refresh_ipi_snapshot()
        trade = await service.refresh_trade_snapshot()
        return {"ipi": ipi, "trade": trade}
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal error during macro ingestion: {exc}") from exc


@router.post("/ipi", response_model=SnapshotEnvelope)
async def ingest_ipi() -> SnapshotEnvelope:
    """
    Fetch the latest Industrial Production Index (IPI) from OpenDOSM,
    calculate the YoY growth, and evaluate macro-economic risk.
    """
    service = build_default_macro_service()
    try:
        return await service.refresh_ipi_snapshot()
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal error during macro ingestion: {exc}")


@router.post("/trade", response_model=SnapshotEnvelope)
async def ingest_trade() -> SnapshotEnvelope:
    """
    Fetch Malaysia External Trade data (exports vs imports) from OpenDOSM.
    Used to derive FX-hedge signals for the AI reasoning layer.
    """
    service = build_default_macro_service()
    try:
        return await service.refresh_trade_snapshot()
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal error during trade ingestion: {exc}")
