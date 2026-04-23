from __future__ import annotations

from app.schemas.common import validate_resin_record


def validate_resin_candidate(candidate: dict) -> None:
    validate_resin_record(candidate)

