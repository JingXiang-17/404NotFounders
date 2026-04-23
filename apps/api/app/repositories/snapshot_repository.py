import json
import logging
from pathlib import Path
from typing import Optional, Literal

from app.core.config import settings
from app.core.exceptions import SnapshotWriteFailed
from app.schemas.common import SnapshotEnvelope

logger = logging.getLogger(__name__)

FreshnessState = Literal["fresh", "stale", "missing"]

class SnapshotRepository:
    def __init__(self, snapshot_dir: Path = settings.SNAPSHOT_DIR):
        self.snapshot_dir = snapshot_dir
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def write_snapshot(self, dataset: str, envelope: SnapshotEnvelope) -> None:
        filename = f"{dataset}_latest.json"
        filepath = self.snapshot_dir / filename
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(envelope.model_dump_json(indent=2))
            logger.info(f"Snapshot written: {filepath}")
        except Exception as e:
            raise SnapshotWriteFailed(f"Failed to write snapshot {dataset}: {str(e)}")

    def read_latest(self, dataset: str) -> Optional[SnapshotEnvelope]:
        filename = f"{dataset}_latest.json"
        filepath = self.snapshot_dir / filename
        if not filepath.exists():
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return SnapshotEnvelope(**data)
        except Exception as e:
            logger.error(f"Failed to read snapshot {dataset}: {e}")
            return None

    def check_freshness(self, dataset: str) -> FreshnessState:
        envelope = self.read_latest(dataset)
        if not envelope:
            return "missing"
        # Can be enhanced to check 'as_of' against current time
        return "fresh"
