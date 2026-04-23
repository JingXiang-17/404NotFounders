import pytest
from app.core.config import Settings

@pytest.fixture
def test_settings():
    """Return settings pointing to test fixtures."""
    return Settings(
        REFERENCE_DIR="../../data/reference",
        SNAPSHOT_DIR="../../data/snapshots",
        SQLITE_PATH=":memory:",
        MODEL_API_KEY="test-key-not-real",
        MODEL_BASE_URL="https://api.z.ai/api/paas/v4/",
        MODEL_NAME="glm-5.1",
    )

@pytest.fixture
def sample_extracted_quote():
    """A known-good extracted quote for testing."""
    from app.schemas.quote import ExtractedQuote
    return ExtractedQuote(
        quote_id="test-q1",
        upload_id="test-u1",
        supplier_name="Ningbo Precision Plastics Co. Ltd.",
        origin_port_or_country="Ningbo",
        incoterm="FOB",
        unit_price=1180.0,
        currency="USD",
        moq=80,
        lead_time_days=35,
        payment_terms="T/T 30 days",
        extraction_confidence=0.92,
    )
