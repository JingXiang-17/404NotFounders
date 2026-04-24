"""
Tests for Langfuse integration hardening.

Ensures that:
- Missing SDK raises at import time (DependencyNotAvailableError).
- Missing credentials raise at _callbacks() time (ProviderError).
- AppSettings.validate_langfuse() raises RuntimeError on missing keys.
- /health/langfuse returns 503 when Langfuse is not enabled.
- Flush failure in trace_url_from_callbacks raises ProviderError.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_provider(*, public_key="pk-test", secret_key="sk-test", host="https://cloud.langfuse.com"):
    """Construct a GLMProvider with the given credentials, bypassing ChatOpenAI init."""
    from app.providers.llm_provider import GLMProvider

    with patch("app.providers.llm_provider.ChatOpenAI") as mock_oai:
        mock_oai.return_value = MagicMock()
        with patch.dict(
            "os.environ",
            {
                "MODEL_API_KEY": "test-key",
                "MODEL_BASE_URL": "https://api.example.com",
                "MODEL_NAME": "ilmu-glm-5.1",
                "LANGFUSE_PUBLIC_KEY": public_key,
                "LANGFUSE_SECRET_KEY": secret_key,
                "LANGFUSE_HOST": host,
            },
            clear=False,
        ):
            provider = GLMProvider.__new__(GLMProvider)
            provider.model_api_key = "test-key"
            provider.model_base_url = "https://api.example.com"
            provider.model_name = "ilmu-glm-5.1"
            provider.langfuse_public_key = public_key or None
            provider.langfuse_secret_key = secret_key or None
            provider.langfuse_host = host or None
            provider.langfuse_project_id = None
            provider.client = MagicMock()
            return provider


# ---------------------------------------------------------------------------
# 1. _callbacks() raises ProviderError when credentials missing
# ---------------------------------------------------------------------------

class TestCallbacksRaisesOnMissingCredentials:
    def test_missing_public_key(self):
        from app.core.exceptions import ProviderError
        provider = _make_provider(public_key="")
        with pytest.raises(ProviderError, match="LANGFUSE_PUBLIC_KEY"):
            provider._callbacks()

    def test_missing_secret_key(self):
        from app.core.exceptions import ProviderError
        provider = _make_provider(secret_key="")
        with pytest.raises(ProviderError, match="LANGFUSE_SECRET_KEY"):
            provider._callbacks()

    def test_missing_host(self):
        from app.core.exceptions import ProviderError
        provider = _make_provider(host="")
        with pytest.raises(ProviderError, match="LANGFUSE_HOST"):
            provider._callbacks()

    def test_all_missing(self):
        from app.core.exceptions import ProviderError
        provider = _make_provider(public_key="", secret_key="", host="")
        with pytest.raises(ProviderError) as exc_info:
            provider._callbacks()
        msg = str(exc_info.value)
        assert "LANGFUSE_PUBLIC_KEY" in msg
        assert "LANGFUSE_SECRET_KEY" in msg
        assert "LANGFUSE_HOST" in msg

    def test_all_present_returns_list(self):
        """When all credentials are present, _callbacks() returns a non-empty list."""
        from app.providers.llm_provider import CallbackHandler
        provider = _make_provider()
        with patch("app.providers.llm_provider.CallbackHandler") as mock_cb:
            mock_cb.return_value = MagicMock()
            callbacks = provider._callbacks()
        assert isinstance(callbacks, list)
        assert len(callbacks) == 1


# ---------------------------------------------------------------------------
# 2. AppSettings.validate_langfuse() raises RuntimeError on missing keys
# ---------------------------------------------------------------------------

class TestSettingsValidateLangfuse:
    def _make_settings(self, *, pk=None, sk=None, host=None):
        from app.core.settings import AppSettings
        from pathlib import Path

        return AppSettings(
            root_dir=Path("/tmp"),
            data_dir=Path("/tmp/data"),
            reference_dir=Path("/tmp/data/reference"),
            snapshot_dir=Path("/tmp/data/snapshots"),
            raw_dir=Path("/tmp/data/raw"),
            tmp_dir=Path("/tmp/data/tmp"),
            langfuse_public_key=pk,
            langfuse_secret_key=sk,
            langfuse_host=host,
        )

    def test_all_missing_raises(self):
        settings = self._make_settings()
        with pytest.raises(RuntimeError) as exc_info:
            settings.validate_langfuse()
        msg = str(exc_info.value)
        assert "LANGFUSE_PUBLIC_KEY" in msg
        assert "LANGFUSE_SECRET_KEY" in msg
        assert "LANGFUSE_HOST" in msg
        assert "[LintasNiaga]" in msg

    def test_partial_missing_raises(self):
        settings = self._make_settings(pk="pk-test", sk=None, host="https://cloud.langfuse.com")
        with pytest.raises(RuntimeError, match="LANGFUSE_SECRET_KEY"):
            settings.validate_langfuse()

    def test_all_present_does_not_raise(self):
        settings = self._make_settings(
            pk="pk-test",
            sk="sk-test",
            host="https://cloud.langfuse.com",
        )
        settings.validate_langfuse()  # Must not raise


# ---------------------------------------------------------------------------
# 3. trace_url_from_callbacks flush raises ProviderError on failure
# ---------------------------------------------------------------------------

class TestFlushRaisesOnError:
    def test_flush_failure_raises_provider_error(self):
        from app.core.exceptions import ProviderError
        from app.providers.llm_provider import GLMProvider

        provider = _make_provider()

        mock_callback = MagicMock()
        mock_callback.last_trace_id = "trace-abc-123"

        def _bad_client():
            bad = MagicMock()
            bad.flush.side_effect = RuntimeError("Langfuse cloud unreachable")
            return bad

        with patch("app.providers.llm_provider.get_client", side_effect=_bad_client):
            with pytest.raises(ProviderError, match="flush failed"):
                provider.trace_url_from_callbacks([mock_callback])


# ---------------------------------------------------------------------------
# 4. /health/langfuse returns 503 when Langfuse not enabled
# ---------------------------------------------------------------------------

class TestLangfuseHealthEndpoint:
    def test_returns_503_when_disabled(self):
        from fastapi.testclient import TestClient
        from app.main import app

        disabled_status = {
            "enabled": False,
            "configured": False,
            "sdk_available": True,
            "host": None,
            "project_id_configured": False,
            "project_id": None,
            "public_key_present": False,
            "secret_key_present": False,
            "trace_url_pattern": None,
        }

        with patch("app.api.routes.health.GLMProvider.langfuse_status", return_value=disabled_status):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/langfuse")

        assert response.status_code == 503
        body = response.json()
        assert "detail" in body
        assert body["detail"]["status"] == "langfuse_unavailable"
        assert "LANGFUSE_PUBLIC_KEY" in body["detail"]["message"] or "LANGFUSE_SECRET_KEY" in body["detail"]["message"]

    def test_returns_200_when_enabled(self):
        from fastapi.testclient import TestClient
        from app.main import app

        enabled_status = {
            "enabled": True,
            "configured": True,
            "sdk_available": True,
            "host": "https://cloud.langfuse.com",
            "project_id_configured": True,
            "project_id": "proj-123",
            "public_key_present": True,
            "secret_key_present": True,
            "trace_url_pattern": "https://cloud.langfuse.com/project/proj-123/traces/<trace_id>",
        }

        with patch("app.api.routes.health.GLMProvider.langfuse_status", return_value=enabled_status):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/langfuse")

        assert response.status_code == 200
        assert response.json()["enabled"] is True
