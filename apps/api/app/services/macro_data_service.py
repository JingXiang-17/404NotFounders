from __future__ import annotations

from typing import Any


class MacroDataService:
    def normalize_series(self, rows: list[dict[str, Any]], *, date_key: str, value_key: str, metric_name: str) -> dict[str, Any]:
        if not rows:
            return {"metric_name": metric_name, "latest_value": None, "previous_value": None, "movement": None, "source_date": None}
        ordered = sorted(rows, key=lambda item: item[date_key])
        latest = ordered[-1]
        previous = ordered[-2] if len(ordered) > 1 else None
        movement = None
        if previous is not None:
            movement = float(latest[value_key]) - float(previous[value_key])
        return {
            "metric_name": metric_name,
            "latest_value": float(latest[value_key]),
            "previous_value": None if previous is None else float(previous[value_key]),
            "movement": movement,
            "source_date": latest[date_key],
        }

