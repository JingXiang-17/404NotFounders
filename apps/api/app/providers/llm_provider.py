from __future__ import annotations

from typing import Protocol

from app.core.exceptions import ProviderError


class ResinLLMProvider(Protocol):
    def extract_resin_benchmark_from_text(self, text: str, *, source_name: str, source_url: str) -> dict:
        """Extract one normalized resin benchmark record."""


class NullLLMProvider:
    def extract_resin_benchmark_from_text(self, text: str, *, source_name: str, source_url: str) -> dict:
        raise ProviderError(
            "No LLM provider is configured. Implement a provider wrapper before running resin extraction."
        )

