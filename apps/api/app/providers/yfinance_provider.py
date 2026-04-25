from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

import pandas as pd
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.constants import DEFAULT_FX_PAIR_TICKERS
from app.core.exceptions import (
    DependencyNotAvailableError,
    ExternalFetchFailed,
    NormalizationFailed,
    ProviderError,
)

try:
    import yfinance as yf  # type: ignore
except ImportError:  # pragma: no cover - exercised through runtime behavior
    yf = None


def _normalize_history_frame(history: pd.DataFrame) -> pd.DataFrame:
    if history.empty:
        raise NormalizationFailed("yfinance returned an empty dataset")

    normalized = history.copy()
    if isinstance(normalized.columns, pd.MultiIndex):
        normalized.columns = [
            str(level_0).lower() if str(level_0).lower() != "price" else str(level_1).lower()
            for level_0, level_1 in normalized.columns.to_flat_index()
        ]
    else:
        normalized.columns = [str(column).lower() for column in normalized.columns]

    normalized = normalized.reset_index()
    normalized.columns = [str(column).lower() for column in normalized.columns]

    if "date" not in normalized.columns:
        datetime_columns = [column for column in normalized.columns if "date" in column]
        if datetime_columns:
            normalized = normalized.rename(columns={datetime_columns[0]: "date"})

    required_columns = ["date", "open", "high", "low", "close"]
    missing_columns = [column for column in required_columns if column not in normalized.columns]
    if missing_columns:
        raise NormalizationFailed(
            f"yfinance payload missing required columns: {', '.join(missing_columns)}"
        )

    normalized = normalized[required_columns].copy()
    normalized["date"] = pd.to_datetime(normalized["date"]).dt.strftime("%Y-%m-%d")
    normalized[["open", "high", "low", "close"]] = normalized[
        ["open", "high", "low", "close"]
    ].astype(float)
    return normalized.sort_values("date").reset_index(drop=True)


class YFinanceMarketDataProvider:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((ProviderError, NormalizationFailed)),
        reraise=True,
    )
    def fetch_history(
        self,
        ticker: str,
        *,
        period: str = "6mo",
        interval: str = "1d",
    ) -> list[dict[str, Any]]:
        if yf is None:
            raise DependencyNotAvailableError(
                "yfinance is not installed. Install project optional dependency 'ingestion'."
            )

        try:
            history = yf.download(
                tickers=ticker,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=False,
                threads=False,
            )
        except Exception as exc:  # pragma: no cover - defensive against provider failures
            raise ProviderError(f"yfinance failed for ticker {ticker}: {exc}") from exc

        normalized = _normalize_history_frame(history)
        return normalized.to_dict(orient="records")


async def fetch_fx_history(pair: str, period: str = "1y") -> pd.DataFrame:
    normalized_pair = pair.upper()
    ticker = DEFAULT_FX_PAIR_TICKERS.get(normalized_pair)
    if not ticker:
        raise ExternalFetchFailed(f"Unsupported FX pair: {pair}")

    provider = YFinanceMarketDataProvider()
    try:
        records = await asyncio.to_thread(provider.fetch_history, ticker, period=period)
        frame = pd.DataFrame(records, columns=["date", "open", "high", "low", "close"])
        if normalized_pair != "CNYMYR" or len(frame) >= 30:
            return frame
    except (ProviderError, DependencyNotAvailableError, NormalizationFailed) as exc:
        if normalized_pair != "CNYMYR":
            raise ExternalFetchFailed(f"Failed to fetch {pair} from yfinance: {exc}") from exc

    if normalized_pair == "CNYMYR":
        try:
            return await _fetch_derived_cnymyr_history(provider=provider, period=period)
        except (ProviderError, DependencyNotAvailableError, NormalizationFailed) as exc:
            raise ExternalFetchFailed(
                f"Failed to derive CNYMYR from yfinance USDMYR and USDCNY history: {exc}"
            ) from exc

    return frame


async def _fetch_derived_cnymyr_history(
    *,
    provider: YFinanceMarketDataProvider,
    period: str,
) -> pd.DataFrame:
    usdmyr_records, usdcny_records = await asyncio.gather(
        asyncio.to_thread(provider.fetch_history, "MYR=X", period=period),
        asyncio.to_thread(provider.fetch_history, "CNY=X", period=period),
    )
    usdmyr = pd.DataFrame(usdmyr_records, columns=["date", "open", "high", "low", "close"])
    usdcny = pd.DataFrame(usdcny_records, columns=["date", "open", "high", "low", "close"])
    merged = usdmyr.merge(usdcny, on="date", suffixes=("_usdmyr", "_usdcny"))
    if merged.empty:
        raise NormalizationFailed("No overlapping dates between USDMYR and USDCNY yfinance histories.")

    derived = pd.DataFrame({"date": merged["date"]})
    for column in ("open", "high", "low", "close"):
        derived[column] = merged[f"{column}_usdmyr"] / merged[f"{column}_usdcny"]

    derived = derived.replace([float("inf"), float("-inf")], pd.NA).dropna()
    if derived.empty:
        raise NormalizationFailed("Derived CNYMYR history had no valid rows after cleaning.")
    return derived.sort_values("date").reset_index(drop=True)


async def fetch_energy_history(symbol: str = "BZ=F", period: str = "1y") -> pd.DataFrame:
    provider = YFinanceMarketDataProvider()
    try:
        records = await asyncio.to_thread(provider.fetch_history, symbol, period=period)
    except (ProviderError, DependencyNotAvailableError, NormalizationFailed) as exc:
        raise ExternalFetchFailed(f"Failed to fetch {symbol} from yfinance: {exc}") from exc

    return pd.DataFrame(records, columns=["date", "open", "high", "low", "close"])
