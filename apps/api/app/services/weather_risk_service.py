from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.openweather_provider import OpenWeatherProvider
from app.repositories.reference_repository import ReferenceRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.schemas.common import SnapshotEnvelope, make_snapshot_envelope

logger = logging.getLogger(__name__)


class WeatherRiskService:
    def __init__(
        self,
        provider: OpenWeatherProvider,
        snapshot_repository: SnapshotRepository,
        reference_repository: ReferenceRepository | None = None,
    ) -> None:
        self.provider = provider
        self.snapshot_repository = snapshot_repository
        self.reference_repository = reference_repository or ReferenceRepository()

    async def refresh_weather_snapshot(self, ports: list[dict[str, Any]] | None = None) -> SnapshotEnvelope:
        if not self.provider.api_key:
            raise ProviderError("OPENWEATHER_API_KEY is not configured.")

        fetched_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        port_list = ports or self._load_reference_ports()
        results = await asyncio.gather(
            *(self._fetch_port_records(port) for port in port_list),
            return_exceptions=True,
        )

        all_records: list[dict[str, Any]] = []
        failed_ports: list[str] = []
        for port, result in zip(port_list, results, strict=False):
            if isinstance(result, Exception):
                logger.warning("Weather fetch failed for %s: %s", port["port_code"], result)
                failed_ports.append(port["port_code"])
                continue
            all_records.extend(result)

        if not all_records:
            latest = self.snapshot_repository.read_latest("weather")
            if latest is None:
                raise ProviderError("OpenWeatherMap failed for all ports and no fallback snapshot exists.")
            return self._partial_from_latest(latest)

        summary = self._summarize_per_port(all_records, port_list)
        envelope = SnapshotEnvelope(
            **make_snapshot_envelope(
                dataset="weather",
                source="openweathermap",
                fetched_at=fetched_at,
                as_of=fetched_at[:10],
                status="partial" if failed_ports else "success",
                data=summary,
            )
        )
        self.snapshot_repository.write_snapshot("weather", envelope)
        logger.info("Weather snapshot written: %d port summaries", len(summary))
        return envelope

    def derive_port_risk(self, forecast_payload: dict[str, Any], port_code: str = "") -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for item in forecast_payload.get("list", []):
            wind_speed = float(item.get("wind", {}).get("speed", 0.0))
            rain_volume = float((item.get("rain") or {}).get("3h", 0.0))
            snow_volume = float((item.get("snow") or {}).get("3h", 0.0))
            precipitation = rain_volume + snow_volume
            risk_score = min(100.0, wind_speed * 5.0 + precipitation * 10.0)
            weather_list = item.get("weather") or [{}]
            entries.append(
                {
                    "port_code": port_code,
                    "forecast_date": item.get("dt_txt", ""),
                    "raw_weather_summary": weather_list[0].get("description", ""),
                    "alert_present": risk_score >= 60.0,
                    "wind_risk_flag": wind_speed >= 12.0,
                    "precipitation_risk_flag": precipitation > 0.0,
                    "wind_speed_ms": round(wind_speed, 2),
                    "precipitation_mm": round(precipitation, 2),
                    "derived_port_risk_score": round(risk_score, 2),
                    "risk_hint": "weather_delay" if risk_score >= 60.0 else "normal_weather",
                    "notes": "Derived from OpenWeatherMap forecast; raw payload is not consumed downstream.",
                }
            )
        return entries

    def get_port_risk_for_context(self) -> list[dict[str, Any]]:
        snapshot = self.snapshot_repository.read_latest("weather")
        if snapshot is None:
            return []
        return snapshot.data or []

    async def _fetch_port_records(self, port: dict[str, Any]) -> list[dict[str, Any]]:
        raw_forecast = await self.provider.fetch_forecast(
            latitude=float(port["latitude"]),
            longitude=float(port["longitude"]),
        )
        return self.derive_port_risk(raw_forecast, port_code=str(port["port_code"]))

    def _load_reference_ports(self) -> list[dict[str, Any]]:
        return [port.model_dump(mode="json") for port in self.reference_repository.get_ports()]

    def _summarize_per_port(
        self,
        all_records: list[dict[str, Any]],
        port_list: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        summary: list[dict[str, Any]] = []
        for port in port_list:
            port_code = str(port["port_code"])
            port_records = [record for record in all_records if record["port_code"] == port_code]
            if not port_records:
                continue
            max_record = max(port_records, key=lambda record: record["derived_port_risk_score"])
            summary.append(
                {
                    "port_code": port_code,
                    "port_name": port.get("port_name", ""),
                    "country_code": port.get("country_code", ""),
                    "max_risk_score": max_record["derived_port_risk_score"],
                    "worst_slot_date": max_record["forecast_date"],
                    "alert_present": any(record["alert_present"] for record in port_records),
                    "wind_risk_flag": any(record["wind_risk_flag"] for record in port_records),
                    "precipitation_risk_flag": any(record["precipitation_risk_flag"] for record in port_records),
                    "raw_weather_summary": max_record["raw_weather_summary"],
                    "risk_hint": max_record["risk_hint"],
                    "notes": max_record["notes"],
                }
            )
        return summary

    @staticmethod
    def _partial_from_latest(latest: SnapshotEnvelope) -> SnapshotEnvelope:
        return SnapshotEnvelope(
            dataset=latest.dataset,
            source=latest.source,
            fetched_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            as_of=latest.as_of,
            status="partial",
            record_count=latest.record_count,
            data=latest.data,
        )


def build_default_weather_service() -> WeatherRiskService:
    return WeatherRiskService(
        OpenWeatherProvider(api_key=settings.OPENWEATHER_API_KEY),
        SnapshotRepository(),
    )
