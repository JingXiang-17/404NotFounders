from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.exceptions import DependencyNotAvailableError, ProviderError

try:
    import yfinance as yf  # type: ignore
except ImportError:  # pragma: no cover - exercised through runtime behavior
    yf = None


class YFinanceMarketDataProvider:
    def fetch_history(self, ticker: str, *, period: str = "6mo", interval: str = "1d") -> list[dict[str, Any]]:
        if yf is None:
            raise DependencyNotAvailableError("yfinance is not installed. Install project optional dependency 'ingestion'.")
        try:
            history = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
        except Exception as exc:  # pragma: no cover - defensive against provider failures
            raise ProviderError(f"yfinance failed for ticker {ticker}: {exc}") from exc

        if history.empty:
            raise ProviderError(f"yfinance returned no rows for ticker {ticker}")

        records: list[dict[str, Any]] = []
        for index, row in history.iterrows():
            date_value = getattr(index, "date", lambda: index)()
            if isinstance(date_value, datetime):
                date_str = date_value.date().isoformat()
            else:
                date_str = str(date_value)
            records.append(
                {
                    "date": date_str,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": None if row.get("Volume") is None else float(row["Volume"]),
                }
            )
        return records

