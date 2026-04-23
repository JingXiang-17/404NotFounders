from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from app.core.constants import DEFAULT_HOLIDAY_COUNTRIES
from app.repositories.snapshot_repository import SnapshotRepository
from app.schemas.common import make_snapshot_envelope, validate_holiday_record


class HolidayService:
    def __init__(self, provider: Any, snapshot_repository: SnapshotRepository) -> None:
        self.provider = provider
        self.snapshot_repository = snapshot_repository

    def ingest_holidays(self, countries: tuple[str, ...] = DEFAULT_HOLIDAY_COUNTRIES, *, window_days: int = 365) -> dict[str, Any]:
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        rows = []
        for country_code in countries:
            for item in self.provider.build_country_window(country_code, start_date=date.today(), days=window_days):
                record = {
                    "country_code": item.country_code,
                    "date": item.date,
                    "holiday_name": item.holiday_name,
                    "is_holiday": item.is_holiday,
                    "is_long_weekend": item.is_long_weekend,
                    "days_until_next_holiday": item.days_until_next_holiday,
                }
                validate_holiday_record(record)
                rows.append(record)
        as_of = min((item["date"] for item in rows), default=None)
        envelope = make_snapshot_envelope(
            dataset="holidays",
            source="python-holidays",
            fetched_at=fetched_at,
            as_of=as_of,
            status="success",
            data=rows,
        )
        path = self.snapshot_repository.write_snapshot("holidays", envelope)
        return {"status": "success", "snapshot_path": str(path), "record_count": len(rows), "fetched_at": fetched_at}

