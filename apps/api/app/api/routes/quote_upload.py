from __future__ import annotations

import importlib.util
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.exceptions import DependencyNotAvailableError, ExtractionFailed, ProviderError
from app.schemas.quote import QuoteRepairRequest, QuoteState
from app.services.quote_ingest_service import (
    get_quote_state,
    get_quote_state_by_upload_id,
    process_upload,
    repair_quote,
)

router = APIRouter(prefix="/quotes", tags=["quotes"])
MULTIPART_AVAILABLE = importlib.util.find_spec("multipart") is not None


if MULTIPART_AVAILABLE:

    @router.post("/upload", response_model=QuoteState)
    async def upload_quote(file: UploadFile = File(...)) -> QuoteState:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF quote uploads are supported.")
        try:
            upload = await process_upload(file)
        except (DependencyNotAvailableError, ExtractionFailed, ProviderError) as exc:
            filename = file.filename or "uploaded file"
            raise HTTPException(
                status_code=502,
                detail=f"Extraction failed for {filename} — please re-upload or enter manually. {str(exc)}",
            ) from exc

        quote_state = get_quote_state_by_upload_id(upload.upload_id)
        if quote_state is None:
            raise HTTPException(status_code=500, detail="Quote upload completed but no quote state was found.")
        return quote_state

else:

    @router.post("/upload")
    async def upload_quote_unavailable() -> dict[str, str]:
        raise HTTPException(
            status_code=503,
            detail='Quote upload requires the optional dependency "python-multipart" to be installed.',
        )

@router.post("/{quote_id}/repair", response_model=QuoteState)
async def repair_uploaded_quote(quote_id: UUID, payload: QuoteRepairRequest) -> QuoteState:
    state = repair_quote(quote_id, payload.model_dump())
    if state is None:
        raise HTTPException(status_code=404, detail="Quote not found.")
    return state


@router.get("/{quote_id}", response_model=QuoteState)
async def get_uploaded_quote(quote_id: UUID) -> QuoteState:
    state = get_quote_state(quote_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Quote not found.")
    return state
