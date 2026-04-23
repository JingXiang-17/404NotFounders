from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal

from pydantic import BaseModel

from app.core.constants import DEFAULT_RESIN_SANE_PRICE_RANGE
from app.core.exceptions import ValidationError


class SnapshotEnvelope(BaseModel):
    dataset: str
    source: str
    fetched_at: str | datetime
    as_of: str | datetime | None
    status: Literal["success", "partial", "failed"]
    record_count: int
    data: List[Any]


SNAPSHOT_REQUIRED_KEYS = {
    "dataset",
    "source",
    "fetched_at",
    "as_of",
    "status",
    "record_count",
    "data",
}
ALLOWED_SNAPSHOT_STATUS = {"success", "partial", "failed"}


def ensure_required_keys(record: dict[str, Any], required_keys: set[str], label: str) -> None:
    missing = sorted(required_keys - set(record))
    if missing:
        raise ValidationError(f"{label} missing required keys: {', '.join(missing)}")


def ensure_iso_date(value: str | None, label: str) -> None:
    if value is None:
        return
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValidationError(f"{label} must be YYYY-MM-DD: {value}") from exc


def ensure_iso_timestamp(value: str, label: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{label} must be ISO-8601: {value}") from exc


def make_snapshot_envelope(
    *,
    dataset: str,
    source: str,
    fetched_at: str,
    as_of: str | None,
    status: str,
    data: list[dict[str, Any]],
) -> dict[str, Any]:
    envelope = {
        "dataset": dataset,
        "source": source,
        "fetched_at": fetched_at,
        "as_of": as_of,
        "status": status,
        "record_count": len(data),
        "data": data,
    }
    validate_snapshot_envelope(envelope)
    return envelope


def validate_snapshot_envelope(envelope: dict[str, Any]) -> None:
    ensure_required_keys(envelope, SNAPSHOT_REQUIRED_KEYS, "Snapshot envelope")
    ensure_iso_timestamp(envelope["fetched_at"], "Snapshot fetched_at")
    ensure_iso_date(envelope["as_of"], "Snapshot as_of")
    if envelope["status"] not in ALLOWED_SNAPSHOT_STATUS:
        raise ValidationError(f"Snapshot status must be one of {sorted(ALLOWED_SNAPSHOT_STATUS)}")
    if not isinstance(envelope["data"], list):
        raise ValidationError("Snapshot data must be a list")
    if envelope["record_count"] != len(envelope["data"]):
        raise ValidationError("Snapshot record_count must match len(data)")


def validate_fx_record(record: dict[str, Any]) -> None:
    ensure_required_keys(record, {"pair", "date", "open", "high", "low", "close"}, "FX record")
    ensure_iso_date(record["date"], "FX date")
    for key in ("open", "high", "low", "close"):
        if not isinstance(record[key], (int, float)):
            raise ValidationError(f"FX {key} must be numeric")
    volume = record.get("volume_optional")
    if volume is not None and not isinstance(volume, (int, float)):
        raise ValidationError("FX volume_optional must be numeric when present")


def validate_energy_record(record: dict[str, Any]) -> None:
    ensure_required_keys(
        record,
        {"symbol", "series_name", "date", "open", "high", "low", "close"},
        "Energy record",
    )
    ensure_iso_date(record["date"], "Energy date")
    for key in ("open", "high", "low", "close"):
        if not isinstance(record[key], (int, float)):
            raise ValidationError(f"Energy {key} must be numeric")


def validate_holiday_record(record: dict[str, Any]) -> None:
    ensure_required_keys(
        record,
        {
            "country_code",
            "date",
            "holiday_name",
            "is_holiday",
            "is_long_weekend",
            "days_until_next_holiday",
        },
        "Holiday record",
    )
    ensure_iso_date(record["date"], "Holiday date")
    if not isinstance(record["is_holiday"], bool):
        raise ValidationError("Holiday is_holiday must be boolean")
    if not isinstance(record["is_long_weekend"], bool):
        raise ValidationError("Holiday is_long_weekend must be boolean")
    if not isinstance(record["days_until_next_holiday"], int):
        raise ValidationError("Holiday days_until_next_holiday must be an integer")


def validate_resin_record(record: dict[str, Any]) -> None:
    ensure_required_keys(
        record,
        {
            "commodity",
            "region",
            "price_value",
            "currency",
            "unit",
            "date_reference",
            "confidence",
            "evidence_snippet",
            "source_name",
            "source_url",
        },
        "Resin record",
    )
    ensure_iso_date(record["date_reference"], "Resin date_reference")
    if record["currency"] != "USD":
        raise ValidationError("Resin currency must be USD")
    if record["unit"] not in {"MT", "USD/MT"}:
        raise ValidationError("Resin unit must be MT or USD/MT")
    if not isinstance(record["price_value"], (int, float)):
        raise ValidationError("Resin price_value must be numeric")
    low, high = DEFAULT_RESIN_SANE_PRICE_RANGE
    if not low <= float(record["price_value"]) <= high:
        raise ValidationError("Resin price_value is outside the accepted sanity range")
    if not isinstance(record["confidence"], (int, float)) or not 0 <= float(record["confidence"]) <= 1:
        raise ValidationError("Resin confidence must be numeric between 0 and 1")
    if not record["evidence_snippet"].strip():
        raise ValidationError("Resin evidence_snippet must be non-empty")
