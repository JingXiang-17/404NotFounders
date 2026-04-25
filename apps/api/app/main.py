import asyncio
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.routes import analysis, health, ingest_holidays, ingest_market, ingest_reference, ingest_macro, ingest_news, ingest_resin, ingest_weather, quote_upload, snapshots
from app.core.constants import DEFAULT_FX_PAIR_TICKERS
from app.core.logging import setup_logging
from app.services.holiday_service import ensure_holiday_snapshot_fresh
from app.services.macro_data_service import build_default_macro_service
from app.services.market_data_service import ensure_energy_snapshot_fresh, ensure_fx_snapshot_fresh
from app.services.news_event_service import build_default_news_service
from app.services.resin_benchmark_service import ensure_resin_snapshot_fresh
from app.services.weather_risk_service import build_default_weather_service

setup_logging()
logger = logging.getLogger(__name__)

MARKET_REFRESH_SECONDS = 24 * 60 * 60
WEATHER_REFRESH_SECONDS = 6 * 60 * 60
MACRO_REFRESH_SECONDS = 24 * 60 * 60
DEFAULT_ENERGY_SYMBOL = "BZ=F"


async def _hourly_news_refresh_loop() -> None:
    service = build_default_news_service()
    while True:
        try:
            envelope = await service.refresh_news_snapshot(keep_history=False)
            logger.info(
                "Hourly GNews refresh succeeded: status=%s rows=%s",
                envelope.status,
                envelope.record_count,
            )
        except Exception as exc:
            logger.error("Hourly GNews refresh failed: %s", exc)
        await asyncio.sleep(60 * 60)


async def _daily_holiday_refresh_loop() -> None:
    while True:
        try:
            envelope = await asyncio.to_thread(ensure_holiday_snapshot_fresh, max_age_hours=24)
            logger.info(
                "Daily holiday refresh ready: status=%s rows=%s",
                envelope.status,
                envelope.record_count,
            )
        except Exception as exc:
            logger.error("Daily holiday refresh failed: %s", exc)
        await asyncio.sleep(24 * 60 * 60)


async def _daily_resin_refresh_loop() -> None:
    while True:
        try:
            envelope = await asyncio.to_thread(ensure_resin_snapshot_fresh, max_age_hours=24)
            logger.info(
                "Daily SunSirs resin refresh ready: status=%s rows=%s",
                envelope.status,
                envelope.record_count,
            )
        except Exception as exc:
            logger.error("Daily SunSirs resin refresh failed: %s", exc)
        await asyncio.sleep(24 * 60 * 60)


async def _daily_market_refresh_loop() -> None:
    while True:
        for pair in DEFAULT_FX_PAIR_TICKERS:
            try:
                envelope = await ensure_fx_snapshot_fresh(pair, max_age_days=1, min_records=30)
                logger.info(
                    "Daily FX refresh ready: pair=%s status=%s as_of=%s rows=%s",
                    pair,
                    envelope.status,
                    envelope.as_of,
                    envelope.record_count,
                )
            except Exception as exc:
                logger.error("Daily FX refresh failed for %s: %s", pair, exc)

        try:
            envelope = await ensure_energy_snapshot_fresh(DEFAULT_ENERGY_SYMBOL, max_age_days=1, min_records=30)
            logger.info(
                "Daily Brent refresh ready: symbol=%s status=%s as_of=%s rows=%s",
                DEFAULT_ENERGY_SYMBOL,
                envelope.status,
                envelope.as_of,
                envelope.record_count,
            )
        except Exception as exc:
            logger.error("Daily Brent refresh failed for %s: %s", DEFAULT_ENERGY_SYMBOL, exc)

        await asyncio.sleep(MARKET_REFRESH_SECONDS)


async def _six_hour_weather_refresh_loop() -> None:
    service = build_default_weather_service()
    while True:
        try:
            envelope = await service.refresh_weather_snapshot(allow_partial=False, keep_history=False)
            logger.info(
                "Scheduled OpenWeather refresh ready: status=%s ports=%s as_of=%s",
                envelope.status,
                envelope.record_count,
                envelope.as_of,
            )
        except Exception as exc:
            logger.error("Scheduled OpenWeather refresh failed: %s", exc)
        await asyncio.sleep(WEATHER_REFRESH_SECONDS)


async def _daily_macro_refresh_loop() -> None:
    service = build_default_macro_service()
    while True:
        try:
            ipi = await service.refresh_ipi_snapshot(keep_history=False)
            trade = await service.refresh_trade_snapshot(keep_history=False)
            logger.info(
                "Daily OpenDOSM refresh ready: ipi_status=%s trade_status=%s ipi_as_of=%s trade_as_of=%s",
                ipi.status,
                trade.status,
                ipi.as_of,
                trade.as_of,
            )
        except Exception as exc:
            logger.error("Daily OpenDOSM refresh failed: %s", exc)
        await asyncio.sleep(MACRO_REFRESH_SECONDS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("LintasNiaga API ready")
    tasks = [
        asyncio.create_task(_hourly_news_refresh_loop()),
        asyncio.create_task(_daily_holiday_refresh_loop()),
        asyncio.create_task(_daily_resin_refresh_loop()),
        asyncio.create_task(_daily_market_refresh_loop()),
        asyncio.create_task(_six_hour_weather_refresh_loop()),
        asyncio.create_task(_daily_macro_refresh_loop()),
    ]
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        for task in tasks:
            with suppress(asyncio.CancelledError):
                await task

app = FastAPI(title="LintasNiaga API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ingest_market.router)
app.include_router(ingest_reference.router)
app.include_router(ingest_holidays.router)
app.include_router(ingest_macro.router)
app.include_router(ingest_news.router)
app.include_router(ingest_resin.router)
app.include_router(ingest_weather.router)
app.include_router(quote_upload.router)
app.include_router(analysis.router)
app.include_router(snapshots.router)
