from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.core.exceptions import ValidationError
from app.core.settings import AppSettings
from app.repositories.reference_repository import ReferenceRepository
from app.services.reference_data_service import ReferenceDataService
from tests.test_utils import workspace_temp_dir


def build_settings(root: Path) -> AppSettings:
    data_dir = root / "data"
    return AppSettings(
        root_dir=root,
        data_dir=data_dir,
        reference_dir=data_dir / "reference",
        snapshot_dir=data_dir / "snapshots",
        raw_dir=data_dir / "raw",
        tmp_dir=data_dir / "tmp",
    )


class ReferenceDataServiceTests(unittest.TestCase):
    def test_reference_validation_passes_for_committed_anchors(self) -> None:
        service = ReferenceDataService(ReferenceRepository(AppSettings.from_env()))
        summary = service.validate_all()
        self.assertEqual(summary["tariffs"], 1)
        self.assertGreaterEqual(summary["freight_rates"], 4)

    def test_reference_validation_rejects_bad_incoterm(self) -> None:
        with workspace_temp_dir() as root:
            reference_dir = root / "data" / "reference"
            reference_dir.mkdir(parents=True)
            committed = AppSettings.from_env().reference_dir
            for name in ("freight_rates.json", "tariffs_my_hs.json", "ports.json", "source_registry.json"):
                data = json.loads((committed / name).read_text(encoding="utf-8"))
                if name == "freight_rates.json":
                    data[0]["incoterm"] = "CIF"
                (reference_dir / name).write_text(json.dumps(data), encoding="utf-8")
            service = ReferenceDataService(ReferenceRepository(build_settings(root)))
            with self.assertRaises(ValidationError):
                service.validate_all()
