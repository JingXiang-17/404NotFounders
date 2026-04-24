from uuid import uuid4

from app.schemas.quote import ExtractedQuote
from app.services.quote_ingest_service import _extract_quote_from_text, _merge_quotes


def test_merge_quotes_uses_base_quote_and_upload_ids():
    quote_id = uuid4()
    upload_id = uuid4()
    page_quote = ExtractedQuote(
        quote_id=uuid4(),
        upload_id=uuid4(),
        supplier_name="Sinopec Ind.",
        origin_port_or_country="China Ningbo",
        incoterm="FOB",
        unit_price=840.0,
        currency="USD",
        moq=80,
        lead_time_days=21,
        payment_terms="30 days",
        extraction_confidence=0.9,
    )

    merged = _merge_quotes(base_quote_id=quote_id, upload_id=upload_id, page_quotes=[page_quote])

    assert merged.quote_id == quote_id
    assert merged.upload_id == upload_id
    assert merged.supplier_name == "Sinopec Ind."
    assert merged.unit_price == 840.0


def test_extract_quote_from_embedded_pdf_text():
    quote = _extract_quote_from_text(
        """
        SAMPLE / DEMO QUOTATION
        Page 1
        SinoPoly Materials Co., Ltd.
        QUOTATION
        Terms: FOB Ningbo, China
        Currency: USD
        Unit Price
        USD 1,018.00 /
        MT
        Incoterm
        FOB Ningbo, China
        MOQ
        80 MT
        Lead Time
        18-21 calendar days after confirmation
        Payment Terms
        20% deposit by T/T, 80% against copy of B/L
        Packing
        25 kg bags
        """
    )

    assert quote is not None
    assert quote.supplier_name == "SinoPoly Materials Co., Ltd."
    assert quote.origin_port_or_country == "FOB Ningbo, China"
    assert quote.incoterm == "FOB"
    assert quote.currency == "USD"
    assert quote.unit_price == 1018.0
    assert quote.moq == 80
    assert quote.lead_time_days == 21
