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

    async def refresh_weather_snapshot(
        self,
        ports: list[dict[str, Any]] | None = None,
        *,
        allow_partial: bool = False,
        keep_history: bool = False,
    ) -> SnapshotEnvelope:
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
            all_records.append(result)

        if not all_records:
            raise ProviderError("OpenWeatherMap failed for all ports.")
        if failed_ports and not allow_partial:
            raise ProviderError(f"OpenWeatherMap failed for required ports: {', '.join(failed_ports)}")

        envelope = SnapshotEnvelope(
            **make_snapshot_envelope(
                dataset="weather",
                source="openweathermap",
                fetched_at=fetched_at,
                as_of=fetched_at[:10],
                status="partial" if failed_ports else "success",
                data=all_records,
            )
        )
        self.snapshot_repository.write_snapshot("weather", envelope, keep_history=keep_history)
        logger.info("Weather snapshot written: %d port summaries", len(all_records))
        return envelope

    def derive_port_risk(self, forecast_payload: dict[str, Any], port_code: str = "") -> list[dict[str, Any]]:
        slots = self._clean_forecast_slots(forecast_payload, port_code=port_code)
        for slot in slots:
            slot["derived_port_risk_score"] = self._weather_risk_score(
                wind_speed_ms=float(slot.get("wind_speed_ms", 0.0)),
                precipitation_mm=float(slot.get("precipitation_mm", 0.0)),
                severe=bool(slot.get("severe_weather_flag", False)),
            )
            slot["alert_present"] = slot["derived_port_risk_score"] >= 60.0
            slot["wind_risk_flag"] = float(slot.get("wind_speed_ms", 0.0)) >= 12.0
            slot["precipitation_risk_flag"] = float(slot.get("precipitation_mm", 0.0)) > 0.0
            slot["risk_hint"] = "weather_delay" if slot["alert_present"] else "normal_weather"
        return slots

    def get_port_risk_for_context(self) -> list[dict[str, Any]]:
        snapshot = self.snapshot_repository.read_latest("weather")
        if snapshot is None:
            return []
        return snapshot.data or []

    async def _fetch_port_records(self, port: dict[str, Any]) -> dict[str, Any]:
        raw_forecast = await self.provider.fetch_forecast(
            latitude=float(port["latitude"]),
            longitude=float(port["longitude"]),
        )
        port_code = str(port["port_code"])
        port_records = self.derive_port_risk(raw_forecast, port_code=port_code)
        if not port_records:
            raise ProviderError(f"OpenWeather returned no forecast rows for {port_code}.")
        return self._summarize_port(
            port=port,
            port_records=port_records,
            endpoint=str(raw_forecast.get("_openweather_endpoint") or "forecast_5_day_3_hour"),
            attempted_endpoints=[str(item) for item in raw_forecast.get("_openweather_attempts", [])],
        )

    def _load_reference_ports(self) -> list[dict[str, Any]]:
        return [port.model_dump(mode="json") for port in self.reference_repository.get_ports()]

    def _summarize_port(
        self,
        *,
        port: dict[str, Any],
        port_records: list[dict[str, Any]],
        endpoint: str,
        attempted_endpoints: list[str],
    ) -> dict[str, Any]:
        max_record = max(port_records, key=lambda record: record["derived_port_risk_score"])
        dates = sorted({str(record["forecast_date"])[:10] for record in port_records if record.get("forecast_date")})
        daily_forecast = self._daily_forecast_summary(port_records)
        high_risk_slots = sorted(
            [record for record in port_records if record["derived_port_risk_score"] >= 60.0],
            key=lambda record: record["derived_port_risk_score"],
            reverse=True,
        )[:10]
        return {
            "port_code": str(port["port_code"]),
            "port_name": port.get("port_name", ""),
            "country_code": port.get("country_code", ""),
            "latitude": port.get("latitude"),
            "longitude": port.get("longitude"),
            "endpoint_used": endpoint,
            "attempted_endpoints": attempted_endpoints,
            "forecast_horizon_days": len(dates),
            "forecast_start_date": dates[0] if dates else "",
            "forecast_end_date": dates[-1] if dates else "",
            "slot_count": len(port_records),
            "max_risk_score": max_record["derived_port_risk_score"],
            "worst_slot_date": max_record["forecast_date"],
            "alert_present": any(record["alert_present"] for record in port_records),
            "wind_risk_flag": any(record["wind_risk_flag"] for record in port_records),
            "precipitation_risk_flag": any(record["precipitation_risk_flag"] for record in port_records),
            "raw_weather_summary": max_record["raw_weather_summary"],
            "risk_hint": max_record["risk_hint"],
            "daily_forecast": daily_forecast,
            "high_risk_slots": high_risk_slots,
            "forecast_slots": port_records,
            "notes": (
                f"Cleaned OpenWeather {endpoint} forecast for {port.get('port_name', port['port_code'])}: "
                f"{len(dates)} day(s), {len(port_records)} slot(s), worst slot {max_record['forecast_date']} "
                f"with {max_record['raw_weather_summary']}."
            ),
        }

    def _clean_forecast_slots(self, forecast_payload: dict[str, Any], *, port_code: str) -> list[dict[str, Any]]:
        endpoint = str(forecast_payload.get("_openweather_endpoint") or "")
        if endpoint == "onecall_8_day":
            return self._clean_onecall_slots(forecast_payload, port_code=port_code)
        return self._clean_list_forecast_slots(forecast_payload, port_code=port_code, daily_mode=endpoint == "forecast_climate_30_day")

    def _clean_list_forecast_slots(
        self,
        forecast_payload: dict[str, Any],
        *,
        port_code: str,
        daily_mode: bool,
    ) -> list[dict[str, Any]]:
        slots: list[dict[str, Any]] = []
        for item in forecast_payload.get("list", []):
            weather_list = item.get("weather") or [{}]
            forecast_date = self._forecast_date(item)
            precipitation = self._precipitation_mm(item, daily_mode=daily_mode)
            wind_speed = self._wind_speed_ms(item)
            description = str(weather_list[0].get("description", ""))
            slots.append(
                {
                    "port_code": port_code,
                    "forecast_date": forecast_date,
                    "slot_type": "daily" if daily_mode else "3_hour",
                    "raw_weather_summary": description,
                    "temperature_c": self._temperature_c(item),
                    "wind_speed_ms": round(wind_speed, 2),
                    "precipitation_mm": round(precipitation, 2),
                    "humidity_pct": item.get("humidity") or item.get("main", {}).get("humidity"),
                    "severe_weather_flag": self._is_severe_weather(description),
                }
            )
        return slots

    def _clean_onecall_slots(self, forecast_payload: dict[str, Any], *, port_code: str) -> list[dict[str, Any]]:
        slots: list[dict[str, Any]] = []
        for item in forecast_payload.get("hourly", []):
            slots.append(self._onecall_item_to_slot(item, port_code=port_code, slot_type="hourly"))
        for item in forecast_payload.get("daily", []):
            slots.append(self._onecall_item_to_slot(item, port_code=port_code, slot_type="daily"))
        return slots

    def _onecall_item_to_slot(self, item: dict[str, Any], *, port_code: str, slot_type: str) -> dict[str, Any]:
        weather_list = item.get("weather") or [{}]
        description = str(weather_list[0].get("description", ""))
        precipitation = self._precipitation_mm(item, daily_mode=slot_type == "daily")
        return {
            "port_code": port_code,
            "forecast_date": self._forecast_date(item),
            "slot_type": slot_type,
            "raw_weather_summary": description,
            "temperature_c": self._temperature_c(item),
            "wind_speed_ms": round(self._wind_speed_ms(item), 2),
            "precipitation_mm": round(precipitation, 2),
            "humidity_pct": item.get("humidity"),
            "severe_weather_flag": self._is_severe_weather(description),
        }

    def _daily_forecast_summary(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_day: dict[str, list[dict[str, Any]]] = {}
        for record in records:
            day = str(record.get("forecast_date", ""))[:10]
            if day:
                by_day.setdefault(day, []).append(record)

        daily: list[dict[str, Any]] = []
        for day, items in sorted(by_day.items()):
            max_item = max(items, key=lambda record: record["derived_port_risk_score"])
            temps = [float(item["temperature_c"]) for item in items if item.get("temperature_c") is not None]
            daily.append(
                {
                    "date": day,
                    "slot_count": len(items),
                    "max_risk_score": max_item["derived_port_risk_score"],
                    "summary": max_item["raw_weather_summary"],
                    "max_wind_speed_ms": max(float(item.get("wind_speed_ms", 0.0)) for item in items),
                    "total_precipitation_mm": round(sum(float(item.get("precipitation_mm", 0.0)) for item in items), 2),
                    "min_temperature_c": round(min(temps), 2) if temps else None,
                    "max_temperature_c": round(max(temps), 2) if temps else None,
                    "alert_present": any(item["alert_present"] for item in items),
                }
            )
        return daily

    @staticmethod
    def _forecast_date(item: dict[str, Any]) -> str:
        if item.get("dt_txt"):
            return str(item["dt_txt"])
        if item.get("dt"):
            return datetime.fromtimestamp(float(item["dt"]), tz=UTC).isoformat().replace("+00:00", "Z")
        return ""

    @staticmethod
    def _temperature_c(item: dict[str, Any]) -> float | None:
        temp = item.get("temp")
        if isinstance(temp, dict):
            value = temp.get("day") or temp.get("max") or temp.get("min")
        else:
            value = temp if temp is not None else item.get("main", {}).get("temp")
        try:
            return round(float(value), 2)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _wind_speed_ms(item: dict[str, Any]) -> float:
        value = item.get("speed") or item.get("wind_speed") or item.get("wind", {}).get("speed") or 0.0
        return float(value or 0.0)

    @staticmethod
    def _precipitation_mm(item: dict[str, Any], *, daily_mode: bool) -> float:
        rain = item.get("rain") or 0.0
        snow = item.get("snow") or 0.0
        if isinstance(rain, dict):
            rain = rain.get("3h") or rain.get("1h") or 0.0
        if isinstance(snow, dict):
            snow = snow.get("3h") or snow.get("1h") or 0.0
        if daily_mode:
            rain = rain or item.get("pop", 0.0)
        return float(rain or 0.0) + float(snow or 0.0)

    @staticmethod
    def _is_severe_weather(description: str) -> bool:
        text = description.lower()
        return any(term in text for term in ("storm", "heavy", "extreme", "squall", "typhoon", "hurricane"))

    @staticmethod
    def _weather_risk_score(*, wind_speed_ms: float, precipitation_mm: float, severe: bool) -> float:
        severe_bonus = 25.0 if severe else 0.0
        return round(min(100.0, wind_speed_ms * 5.0 + precipitation_mm * 10.0 + severe_bonus), 2)


def build_default_weather_service() -> WeatherRiskService:
    return WeatherRiskService(
        OpenWeatherProvider(api_key=settings.OPENWEATHER_API_KEY),
        SnapshotRepository(),
    )
