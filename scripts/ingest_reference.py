from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.core.exceptions import IngestionError
from app.core.settings import AppSettings
from app.repositories.reference_repository import ReferenceRepository
from app.services.reference_data_service import ReferenceDataService


def main() -> int:
    try:
        settings = AppSettings.from_env()
        service = ReferenceDataService(ReferenceRepository(settings))
        summary = service.validate_all()
        print(summary)
        return 0
    except IngestionError as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
