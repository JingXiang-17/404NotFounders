from __future__ import annotations


class WeatherRiskService:
    def derive_port_risk(self, forecast_payload: dict) -> list[dict]:
        """Normalize raw weather payloads into lightweight port-risk records."""
        entries = []
        for item in forecast_payload.get("list", []):
            wind_speed = float(item.get("wind", {}).get("speed", 0.0))
            rain_volume = float(item.get("rain", {}).get("3h", 0.0))
            risk_score = min(100.0, wind_speed * 5.0 + rain_volume * 10.0)
            entries.append(
                {
                    "forecast_date": item.get("dt_txt", ""),
                    "raw_weather_summary": item.get("weather", [{}])[0].get("description", ""),
                    "alert_present": risk_score >= 60.0,
                    "wind_risk_flag": wind_speed >= 12.0,
                    "precipitation_risk_flag": rain_volume > 0.0,
                    "derived_port_risk_score": round(risk_score, 2),
                    "notes": "Derived from forecast payload; do not consume raw weather payload downstream.",
                }
            )
        return entries

