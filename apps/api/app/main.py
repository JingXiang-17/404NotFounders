from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.routes import analysis, health, ingest_holidays, ingest_market, ingest_reference, ingest_macro, ingest_news, ingest_resin, ingest_weather, quote_upload, snapshots
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("LintasNiaga API ready")
    yield

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
