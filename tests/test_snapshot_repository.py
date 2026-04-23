from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.core.settings import AppSettings
from app.repositories.snapshot_repository import SnapshotRepository
from app.schemas.common import make_snapshot_envelope
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


class SnapshotRepositoryTests(unittest.TestCase):
    def test_latest_pointer_is_updated_on_write(self) -> None:
        with workspace_temp_dir() as root:
            settings = build_settings(root)
            repository = SnapshotRepository(settings)
            envelope = make_snapshot_envelope(
                dataset="fx",
                source="test",
                fetched_at="2026-04-23T10:00:00Z",
                as_of="2026-04-22",
                status="success",
                data=[{"pair": "USDMYR", "date": "2026-04-22", "open": 4.2, "high": 4.3, "low": 4.1, "close": 4.25}],
            )
            path = repository.write_snapshot("fx", envelope)
            self.assertTrue(path.exists())
            latest = repository.load_latest("fx")
            self.assertIsNotNone(latest)
            self.assertEqual(latest["record_count"], 1)
