from fastapi import APIRouter, HTTPException

from app.core.exceptions import ProviderError
from app.services.news_event_service import build_default_news_service
from app.schemas.common import SnapshotEnvelope

router = APIRouter(prefix="/ingest/news", tags=["ingestion"])


@router.post("/gnews", response_model=SnapshotEnvelope)
async def ingest_gnews() -> SnapshotEnvelope:
    """
    Fetch GNews articles across logistics + finance buckets,
    normalize into event records, and write to news snapshot.
    """
    service = build_default_news_service()
    try:
        return await service.refresh_news_snapshot()
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal error during news ingestion: {exc}")
