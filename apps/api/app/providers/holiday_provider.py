from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import holidays

from app.core.exceptions import ProviderError


@dataclass(frozen=True)
class HolidayWindow:
    country_code: str
    date: str
    holiday_name: str
    is_holiday: bool
    is_long_weekend: bool
    days_until_next_holiday: int


class HolidayProvider:
    def build_country_window(self, country_code: str, *, start_date: date, days: int = 365) -> list[HolidayWindow]:
        try:
            calendar = holidays.country_holidays(country_code, years={start_date.year, (start_date + timedelta(days=days)).year})
        except Exception as exc:
            raise ProviderError(f"Unable to build holiday calendar for {country_code}: {exc}") from exc

        results: list[HolidayWindow] = []
        holiday_dates = sorted(calendar.keys())
        for offset in range(days):
            current_date = start_date + timedelta(days=offset)
            holiday_name = calendar.get(current_date)
            next_holiday = next((item for item in holiday_dates if item >= current_date), None)
            days_until = 0 if next_holiday is None else (next_holiday - current_date).days
            is_holiday = holiday_name is not None
            is_long_weekend = is_holiday and current_date.weekday() in {0, 4}
            results.append(
                HolidayWindow(
                    country_code=country_code,
                    date=current_date.isoformat(),
                    holiday_name=holiday_name or "",
                    is_holiday=is_holiday,
                    is_long_weekend=is_long_weekend,
                    days_until_next_holiday=days_until,
                )
            )
        return results

