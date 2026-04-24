from __future__ import annotations

import base64
import json
import os
from typing import Any, Protocol
from uuid import uuid4

from app.core.exceptions import DependencyNotAvailableError, ProviderError
from app.core.settings import AppSettings
from app.schemas.quote import ExtractedQuote

try:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - runtime dependency
    ChatOpenAI = None
    HumanMessage = None
    SystemMessage = None

try:
    from langfuse import Langfuse, get_client
    from langfuse.langchain import CallbackHandler
except ImportError:  # pragma: no cover - runtime dependency
    CallbackHandler = None
    get_client = None
    Langfuse = None


EXTRACTION_PROMPT = (
    "Extract the following fields from this supplier quotation image as JSON: "
    "supplier_name, origin_port_or_country, incoterm, unit_price (numeric), "
    "currency (ISO 4217), moq (integer), lead_time_days (integer), payment_terms. "
    "Return only valid JSON, no markdown."
)


class ResinLLMProvider(Protocol):
    def extract_resin_benchmark_from_text(self, text: str, *, source_name: str, source_url: str) -> dict:
        """Extract one normalized resin benchmark record."""


class NullLLMProvider:
    def extract_resin_benchmark_from_text(self, text: str, *, source_name: str, source_url: str) -> dict:
        raise ProviderError(
            "No LLM provider is configured. Implement a provider wrapper before running resin extraction."
        )


class GLMProvider:
    def __init__(self) -> None:
        settings = AppSettings.from_env()
        self.model_api_key = os.getenv("MODEL_API_KEY") or settings.model_api_key
        self.model_base_url = os.getenv("MODEL_BASE_URL")
        self.model_name = os.getenv("MODEL_NAME", "glm-5.1")
        self.langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        self.langfuse_host = os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST")
        self.langfuse_project_id = os.getenv("LANGFUSE_PROJECT_ID")
        if self.langfuse_host and not os.getenv("LANGFUSE_BASE_URL"):
            # Langfuse SDK v3/v4 uses LANGFUSE_BASE_URL; older docs/examples
            # often used LANGFUSE_HOST. Keep the existing .env compatible.
            os.environ["LANGFUSE_BASE_URL"] = self.langfuse_host
        if Langfuse and self.langfuse_public_key and self.langfuse_secret_key and self.langfuse_host:
            Langfuse(
                public_key=self.langfuse_public_key,
                secret_key=self.langfuse_secret_key,
                base_url=self.langfuse_host,
            )

        if ChatOpenAI is None or HumanMessage is None or SystemMessage is None:
            raise DependencyNotAvailableError(
                "langchain_openai and langchain_core are required for LLM quote extraction."
            )
        if not self.model_api_key:
            raise ProviderError("MODEL_API_KEY is not configured for GLM quote extraction.")

        self.client = ChatOpenAI(
            model=self.model_name,
            openai_api_key=self.model_api_key,
            openai_api_base=self.model_base_url,
            temperature=0,
            max_tokens=4000,
        )

    def _callbacks(self) -> list[Any]:
        if not CallbackHandler:
            return []
        if not (self.langfuse_public_key and self.langfuse_secret_key and self.langfuse_host):
            return []
        return [CallbackHandler(public_key=self.langfuse_public_key)]

    def trace_url_from_callbacks(self, callbacks: list[Any]) -> str | None:
        if get_client is None:
            return None
        trace_id = next(
            (
                getattr(callback, "last_trace_id", None)
                for callback in callbacks
                if getattr(callback, "last_trace_id", None)
            ),
            None,
        )
        if not trace_id:
            return None
        if self.langfuse_host and self.langfuse_project_id:
            return f"{self.langfuse_host.rstrip('/')}/project/{self.langfuse_project_id}/traces/{trace_id}"
        try:
            public_key = getattr(callbacks[0], "public_key", None) if callbacks else None
            client = get_client(public_key=public_key) if public_key else get_client()
            if hasattr(client, "flush"):
                client.flush()
            return client.get_trace_url(trace_id=trace_id)
        except Exception:
            return None

    @staticmethod
    def _clean_json(raw_text: str) -> dict[str, Any]:
        content = raw_text.strip()
        if content.startswith("```"):
            parts = content.split("```")
            content = next((part for part in parts if "{" in part and "}" in part), content)
            content = content.replace("json", "", 1).strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise ProviderError(f"LLM did not return valid JSON: {content}") from exc

    def extract_quote_fields(self, image_bytes: bytes) -> ExtractedQuote:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        messages = [
            SystemMessage(
                content=(
                    "You extract structured procurement fields from supplier quotation images. "
                    "Return strict JSON only."
                )
            ),
            HumanMessage(
                content=[
                    {"type": "text", "text": EXTRACTION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ]
            ),
        ]

        try:
            response = self.client.invoke(messages, config={"callbacks": self._callbacks()})
        except Exception as exc:
            raise ProviderError(f"Quote extraction model request failed: {exc}") from exc
        payload = self._clean_json(response.content if isinstance(response.content, str) else str(response.content))

        return ExtractedQuote(
            quote_id=uuid4(),
            upload_id=uuid4(),
            supplier_name=payload.get("supplier_name"),
            origin_port_or_country=payload.get("origin_port_or_country"),
            incoterm=payload.get("incoterm"),
            unit_price=float(payload["unit_price"]) if payload.get("unit_price") is not None else None,
            currency=payload.get("currency"),
            moq=int(payload["moq"]) if payload.get("moq") is not None else None,
            lead_time_days=int(payload["lead_time_days"]) if payload.get("lead_time_days") is not None else None,
            payment_terms=payload.get("payment_terms"),
            extraction_confidence=None,
        )

    def reason_about_recommendation(self, context: dict[str, Any]) -> str:
        try:
            response = self.client.invoke(
                [
                    SystemMessage(content="You are LintasNiaga's procurement analyst."),
                    HumanMessage(content=json.dumps(context, ensure_ascii=True)),
                ],
                config={"callbacks": self._callbacks()},
            )
        except Exception as exc:
            raise ProviderError(f"Recommendation reasoning request failed: {exc}") from exc
        return response.content if isinstance(response.content, str) else str(response.content)


def build_llm_provider() -> GLMProvider:
    return GLMProvider()

