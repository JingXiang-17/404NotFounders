from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile

try:
    import fitz
except ImportError:  # pragma: no cover - runtime dependency
    fitz = None

from app.core.exceptions import DependencyNotAvailableError, ExtractionFailed
from app.core.settings import AppSettings
from app.providers.llm_provider import build_llm_provider
from app.schemas.quote import ExtractedQuote, QuoteState, QuoteUpload
from app.services.quote_validation_service import validate_quote

QUOTE_STATES: dict[UUID, QuoteState] = {}


def _upload_dir() -> Path:
    settings = AppSettings.from_env()
    configured = os.getenv("UPLOAD_DIR")
    if configured:
        return Path(configured)
    return settings.root_dir / "apps" / "api" / "uploads"


def _merge_quotes(base_quote_id: UUID, upload_id: UUID, page_quotes: list[ExtractedQuote]) -> ExtractedQuote:
    merged = ExtractedQuote(quote_id=base_quote_id, upload_id=upload_id)
    fields = [
        "supplier_name",
        "origin_port_or_country",
        "incoterm",
        "unit_price",
        "currency",
        "moq",
        "lead_time_days",
        "payment_terms",
    ]
    confidences = [quote.extraction_confidence for quote in page_quotes if quote.extraction_confidence is not None]

    for field_name in fields:
        for quote in page_quotes:
            value = getattr(quote, field_name)
            if value is not None and (not isinstance(value, str) or value.strip()):
                setattr(merged, field_name, value)
                break

    merged.extraction_confidence = sum(confidences) / len(confidences) if confidences else None
    return merged


def _render_first_two_pages(pdf_bytes: bytes) -> list[bytes]:
    if fitz is None:
        raise DependencyNotAvailableError("PyMuPDF (fitz) is required for quote PDF rendering.")
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise ExtractionFailed(f"Failed to open uploaded PDF: {exc}") from exc

    images: list[bytes] = []
    for page_index in range(min(2, document.page_count)):
        page = document.load_page(page_index)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        images.append(pixmap.tobytes("png"))
    document.close()
    if not images:
        raise ExtractionFailed("Uploaded PDF has no renderable pages.")
    return images


def _extract_text_pages(pdf_bytes: bytes) -> list[str]:
    if fitz is None:
        return []
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        return []

    pages: list[str] = []
    for page_index in range(min(2, document.page_count)):
        pages.append(document.load_page(page_index).get_text())
    document.close()
    return pages


def _extract_quote_from_text(text: str) -> ExtractedQuote | None:
    normalized = text.replace("\r\n", "\n")
    if "QUOTATION" not in normalized.upper():
        return None

    supplier_name = _first_match(normalized, r"Page\s+\d+\s*\n(?P<value>.+?)\n")
    terms = _first_match(normalized, r"Terms:\s*(?P<value>FOB[^\n]+)")
    origin = _first_match(normalized, r"Origin:\s*(?P<value>FOB[^\n]+)") or terms
    incoterm = "FOB" if (terms and terms.upper().startswith("FOB")) or (origin and origin.upper().startswith("FOB")) else None
    currency = _first_match(normalized, r"Currency:\s*(?P<value>[A-Z]{3})")

    unit_price = None
    price_match = re.search(
        r"\b(?P<currency>USD|CNY|THB|IDR)\s+(?P<price>[\d,]+(?:\.\d+)?)\s*/\s*(?:\n\s*)?MT\b",
        normalized,
        flags=re.IGNORECASE,
    )
    if price_match:
        currency = currency or price_match.group("currency").upper()
        unit_price = float(price_match.group("price").replace(",", ""))

    moq = _first_int(normalized, r"MOQ\s*\n\s*(?P<value>\d+)\s*MT")
    lead_start = _first_int(normalized, r"Lead Time\s*\n\s*(?P<value>\d+)(?:-\d+)?")
    lead_end = _first_int(normalized, r"Lead Time\s*\n\s*\d+-(?P<value>\d+)")
    lead_time_days = lead_end or lead_start
    payment_terms = _first_match(normalized, r"Payment Terms\s*\n\s*(?P<value>.+?)(?:\n\s*Packing|\n\s*Price Basis)")

    return ExtractedQuote(
        quote_id=uuid4(),
        upload_id=uuid4(),
        supplier_name=supplier_name,
        origin_port_or_country=origin,
        incoterm=incoterm,
        unit_price=unit_price,
        currency=currency,
        moq=moq,
        lead_time_days=lead_time_days,
        payment_terms=payment_terms,
        extraction_confidence=0.98,
    )


def _first_match(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    value = match.group("value").strip()
    return re.sub(r"\s+", " ", value) if value else None


def _first_int(text: str, pattern: str) -> int | None:
    value = _first_match(text, pattern)
    return int(value) if value and value.isdigit() else None


async def process_upload(file: UploadFile) -> QuoteUpload:
    upload_id = uuid4()
    quote_id = uuid4()
    upload_dir = _upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)

    pdf_bytes = await file.read()
    storage_path = upload_dir / f"{upload_id}_{file.filename}"
    storage_path.write_bytes(pdf_bytes)

    upload = QuoteUpload(
        upload_id=upload_id,
        filename=file.filename or f"{upload_id}.pdf",
        storage_path=str(storage_path),
        uploaded_at=datetime.now(UTC),
        status="pending",
    )
    QUOTE_STATES[quote_id] = QuoteState(upload=upload)

    text_pages = _extract_text_pages(pdf_bytes)
    extracted_pages = [
        quote for quote in (_extract_quote_from_text(text_page) for text_page in text_pages) if quote is not None
    ]
    if not extracted_pages or validate_quote(_merge_quotes(base_quote_id=quote_id, upload_id=upload_id, page_quotes=extracted_pages)).status != "valid":
        provider = build_llm_provider()
        page_images = _render_first_two_pages(pdf_bytes)
        extracted_pages = [provider.extract_quote_fields(image_bytes) for image_bytes in page_images]
    merged_quote = _merge_quotes(base_quote_id=quote_id, upload_id=upload_id, page_quotes=extracted_pages)
    validation = validate_quote(merged_quote)

    upload.status = "validated" if validation.status == "valid" else "invalid"
    QUOTE_STATES[quote_id] = QuoteState(
        upload=upload,
        extracted_quote=merged_quote,
        validation=validation,
    )
    return upload


def get_quote_state(quote_id: UUID) -> QuoteState | None:
    return QUOTE_STATES.get(quote_id)


def get_quote_state_by_upload_id(upload_id: UUID) -> QuoteState | None:
    for state in QUOTE_STATES.values():
        if state.upload.upload_id == upload_id:
            return state
    return None


def repair_quote(quote_id: UUID, updates: dict[str, object]) -> QuoteState | None:
    state = QUOTE_STATES.get(quote_id)
    if state is None or state.extracted_quote is None:
        return None

    updated_payload = state.extracted_quote.model_dump()
    for key, value in updates.items():
        if value is not None and key in updated_payload:
            updated_payload[key] = value
    repaired_quote = ExtractedQuote(**updated_payload)
    validation = validate_quote(repaired_quote)
    state.upload.status = "validated" if validation.status == "valid" else "invalid"
    updated_state = QuoteState(upload=state.upload, extracted_quote=repaired_quote, validation=validation)
    QUOTE_STATES[quote_id] = updated_state
    return updated_state
