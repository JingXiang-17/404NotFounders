from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.core.exceptions import IngestionError
from app.core.settings import AppSettings
from app.providers.yfinance_provider import YFinanceMarketDataProvider
from app.repositories.snapshot_repository import SnapshotRepository
from app.services.market_data_service import MarketDataService


def main() -> int:
    try:
        settings = AppSettings.from_env()
        service = MarketDataService(YFinanceMarketDataProvider(), SnapshotRepository(settings))
        result = service.ingest_fx()
        print(result)
        return 0
    except IngestionError as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
