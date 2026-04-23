from __future__ import annotations

import re

from app.core.exceptions import ValidationError
from app.repositories.reference_repository import ReferenceRepository


class ResinSourceRegistry:
    def __init__(self, repository: ReferenceRepository) -> None:
        self.repository = repository

    def enabled_sources(self) -> list[dict]:
        sources = self.repository.load_json("source_registry.json")
        return [source for source in sources if source.get("enabled")]

    def select_primary_source(self) -> dict:
        sources = sorted(self.enabled_sources(), key=lambda item: item["priority"])
        if not sources:
            raise ValidationError("No enabled resin sources found in source_registry.json")
        return sources[0]

    @staticmethod
    def slugify(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

