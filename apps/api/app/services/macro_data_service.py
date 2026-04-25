from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.core.exceptions import ProviderError
from app.providers.opendosm_provider import OpenDOSMProvider
from app.repositories.snapshot_repository import SnapshotRepository
from app.schemas.common import SnapshotEnvelope, make_snapshot_envelope


class MacroDataService:
    def __init__(self, provider: OpenDOSMProvider, snapshot_repository: SnapshotRepository) -> None:
        self.provider = provider
        self.snapshot_repository = snapshot_repository

    async def refresh_ipi_snapshot(
        self,
        *,
        allow_partial: bool = False,
        keep_history: bool = False,
    ) -> SnapshotEnvelope:
        fetched_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        try:
            rows = await self.provider.fetch_dataset("ipi", limit=200)
        except Exception as exc:
            return self._fallback_or_raise("macro", f"OpenDOSM IPI failed: {exc}", allow_partial=allow_partial)

        record = self._build_ipi_risk_record(rows)
        envelope = SnapshotEnvelope(
            **make_snapshot_envelope(
                dataset="macro",
                source="opendosm:ipi",
                fetched_at=fetched_at,
                as_of=record["source_date"],
                status="success",
                data=[record],
            )
        )
        self.snapshot_repository.write_snapshot("macro", envelope, keep_history=keep_history)
        return envelope

    async def refresh_trade_snapshot(
        self,
        *,
        allow_partial: bool = False,
        keep_history: bool = False,
    ) -> SnapshotEnvelope:
        fetched_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        try:
            rows = await self.provider.fetch_dataset("trade_sitc_1d", limit=500)
        except Exception as exc:
            return self._fallback_or_raise("macro_trade", f"OpenDOSM trade failed: {exc}", allow_partial=allow_partial)

        record = self._build_trade_risk_record(rows)
        envelope = SnapshotEnvelope(
            **make_snapshot_envelope(
                dataset="macro_trade",
                source="opendosm:trade_sitc_1d",
                fetched_at=fetched_at,
                as_of=record["source_date"],
                status="success" if record["status"] != "UNKNOWN" else "partial",
                data=[record],
            )
        )
        self.snapshot_repository.write_snapshot("macro_trade", envelope, keep_history=keep_history)
        return envelope

    def normalize_series(
        self,
        rows: list[dict[str, Any]],
        *,
        date_key: str,
        value_key: str,
        metric_name: str,
    ) -> dict[str, Any]:
        if not rows:
            return {
                "metric_name": metric_name,
                "latest_value": None,
                "previous_value": None,
                "movement": None,
                "source_date": None,
            }
        ordered = sorted(rows, key=lambda item: item[date_key])
        latest = ordered[-1]
        previous = ordered[-2] if len(ordered) > 1 else None
        movement = None
        if previous is not None:
            movement = self._to_float(latest[value_key]) - self._to_float(previous[value_key])
        return {
            "metric_name": metric_name,
            "latest_value": self._to_float(latest[value_key]),
            "previous_value": None if previous is None else self._to_float(previous[value_key]),
            "movement": movement,
            "source_date": latest[date_key],
        }

    def get_macro_context_for_ai(self) -> dict[str, Any]:
        context: dict[str, Any] = {}
        ipi_snap = self.snapshot_repository.read_latest("macro")
        trade_snap = self.snapshot_repository.read_latest("macro_trade")
        if ipi_snap and ipi_snap.data:
            context["ipi"] = ipi_snap.data[0]
        if trade_snap and trade_snap.data:
            context["trade"] = trade_snap.data[0]
        return context

    def _fallback_or_raise(self, dataset: str, message: str, *, allow_partial: bool) -> SnapshotEnvelope:
        latest = self.snapshot_repository.read_latest(dataset)
        if latest is None or not allow_partial:
            raise ProviderError(message)
        return SnapshotEnvelope(
            dataset=latest.dataset,
            source=latest.source,
            fetched_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            as_of=latest.as_of,
            status="partial",
            record_count=latest.record_count,
            data=latest.data,
        )

    def _build_ipi_risk_record(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        yoy_rows = [
            row
            for row in rows
            if str(row.get("series_type", "")).lower() == "growth_yoy"
            and self._row_mentions(row, {"manufacturing", "pembuatan", "overall", "total"})
        ]
        if not yoy_rows:
            yoy_rows = [row for row in rows if str(row.get("series_type", "")).lower() == "growth_yoy"]
        if yoy_rows:
            latest = self._latest_by_date(yoy_rows)
            latest_date = self._date_value(latest)
            growth_rate = self._to_float(latest.get("index"))
        else:
            latest, comparison = self._latest_and_year_ago_index(rows)
            latest_date = self._date_value(latest)
            latest_index = self._to_float(latest.get("index"))
            comparison_index = self._to_float(comparison.get("index"))
            growth_rate = round(((latest_index - comparison_index) / comparison_index) * 100, 2)
        danger = growth_rate < 0
        return {
            "metric_name": "IPI_YoY_Growth",
            "dataset_id": "ipi",
            "source_date": latest_date,
            "growth_rate_pct": growth_rate,
            "status": "DANGER" if danger else "SAFE",
            "risk_driver": "dead_stock" if danger else "normal_inventory",
            "message": (
                f"OpenDOSM reports Malaysian manufacturing contracted by {growth_rate}% in {latest_date}."
                if danger
                else f"OpenDOSM reports Malaysian manufacturing grew by {growth_rate}% in {latest_date}."
            ),
            "ai_action": (
                "Warn user to reduce MOQ to avoid dead stock."
                if danger
                else "Market is healthy. Standard MOQ is safe."
            ),
        }

    def _build_trade_risk_record(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        latest_date = max((self._date_value(row) for row in rows if self._date_value(row)), default=None)
        if latest_date is None:
            raise ProviderError("OpenDOSM trade data did not include dated rows.")

        latest_rows = [row for row in rows if self._date_value(row) == latest_date]
        exports, imports = self._extract_trade_totals(latest_rows)
        if exports is None or imports is None:
            return {
                "metric_name": "Malaysia_Trade_Balance",
                "dataset_id": "trade_sitc_1d",
                "source_date": latest_date,
                "exports": exports,
                "imports": imports,
                "trade_balance": None,
                "status": "UNKNOWN",
                "risk_driver": "fx_hedge",
                "message": "OpenDOSM trade data was fetched, but export/import fields were not recognized.",
                "ai_action": "Do not use trade balance as a hedge signal until the field mapping is reviewed.",
            }

        trade_balance = exports - imports
        danger = trade_balance < 0
        return {
            "metric_name": "Malaysia_Trade_Balance",
            "dataset_id": "trade_sitc_1d",
            "source_date": latest_date,
            "exports": exports,
            "imports": imports,
            "trade_balance": trade_balance,
            "status": "DANGER" if danger else "SAFE",
            "risk_driver": "fx_hedge" if danger else "fx_monitor",
            "message": (
                f"Malaysia trade deficit of {abs(trade_balance):,.0f} in {latest_date}. MYR may weaken."
                if danger
                else f"Malaysia trade surplus of {trade_balance:,.0f} in {latest_date}. Export base is healthy."
            ),
            "ai_action": (
                "Recommend hedging FX exposure or staggering purchases."
                if danger
                else "FX macro risk is moderate. Standard procurement timing is acceptable."
            ),
        }

    def _extract_trade_totals(self, rows: list[dict[str, Any]]) -> tuple[float | None, float | None]:
        for row in rows:
            exports = self._first_float(row, ("exports", "export", "total_exports", "eksport"))
            imports = self._first_float(row, ("imports", "import", "total_imports", "import"))
            if exports is not None and imports is not None:
                return exports, imports

        exports_total = 0.0
        imports_total = 0.0
        found_exports = False
        found_imports = False
        for row in rows:
            flow = " ".join(str(row.get(key, "")).lower() for key in ("flow", "trade_flow", "type", "indicator"))
            value = self._first_float(row, ("value", "amount", "trade_value", "rm", "index"))
            if value is None:
                continue
            if "export" in flow or "eksport" in flow:
                exports_total += value
                found_exports = True
            elif "import" in flow:
                imports_total += value
                found_imports = True
        return (
            exports_total if found_exports else None,
            imports_total if found_imports else None,
        )

    @staticmethod
    def _latest_by_date(rows: list[dict[str, Any]]) -> dict[str, Any]:
        return sorted(rows, key=lambda row: str(row.get("date", "")), reverse=True)[0]

    def _latest_and_year_ago_index(
        self,
        rows: list[dict[str, Any]],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        absolute_rows = [
            row
            for row in rows
            if str(row.get("series", "")).lower() in {"abs", "absolute", ""}
            and row.get("index") not in (None, "")
            and self._date_value(row)
        ]
        if len(absolute_rows) < 13:
            raise ProviderError("OpenDOSM IPI data did not contain enough absolute index rows for YoY calculation.")

        ordered = sorted(absolute_rows, key=self._date_value)
        latest = ordered[-1]
        latest_date = self._date_value(latest)
        target_year_ago = f"{int(latest_date[:4]) - 1}{latest_date[4:]}"
        for row in reversed(ordered[:-1]):
            if self._date_value(row) == target_year_ago:
                return latest, row
        return latest, ordered[-13]

    @staticmethod
    def _date_value(row: dict[str, Any]) -> str:
        return str(row.get("date") or row.get("period") or "")

    @staticmethod
    def _row_mentions(row: dict[str, Any], needles: set[str]) -> bool:
        haystack = " ".join(str(value).lower() for value in row.values())
        return any(needle in haystack for needle in needles)

    @classmethod
    def _first_float(cls, row: dict[str, Any], keys: tuple[str, ...]) -> float | None:
        for key in keys:
            if key in row and row[key] not in (None, ""):
                return cls._to_float(row[key])
        return None

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            return float(str(value).replace(",", ""))
        except (TypeError, ValueError) as exc:
            raise ProviderError(f"Expected numeric value from OpenDOSM, got {value!r}") from exc


def build_default_macro_service() -> MacroDataService:
    return MacroDataService(OpenDOSMProvider(), SnapshotRepository())
