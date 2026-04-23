from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Literal, Optional

from app.core.exceptions import SnapshotWriteFailed
from app.core.settings import AppSettings
from app.schemas.common import SnapshotEnvelope, validate_snapshot_envelope

logger = logging.getLogger(__name__)

FreshnessState = Literal["fresh", "stale", "missing"]


class SnapshotRepository:
    def __init__(self, snapshot_root: Any = None) -> None:
        if hasattr(snapshot_root, "snapshot_dir"):
            self.snapshot_dir = Path(snapshot_root.snapshot_dir)
        elif snapshot_root is None:
            self.snapshot_dir = Path(AppSettings.from_env().snapshot_dir)
        else:
            self.snapshot_dir = Path(snapshot_root)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def write_snapshot(self, dataset: str, envelope: SnapshotEnvelope | dict[str, Any]) -> Path:
        payload = envelope.model_dump(mode="json") if isinstance(envelope, SnapshotEnvelope) else envelope
        validate_snapshot_envelope(payload)
        dataset_dir = self.snapshot_dir / dataset
        dataset_dir.mkdir(parents=True, exist_ok=True)
        timestamp = payload["fetched_at"].replace(":", "").replace("-", "").replace("T", "_").replace("Z", "Z")
        versioned_path = dataset_dir / f"{dataset}_{timestamp}.json"
        latest_path = dataset_dir / "latest.json"
        try:
            versioned_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            latest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            logger.info("Snapshot written: %s", versioned_path)
            return versioned_path
        except Exception as exc:
            raise SnapshotWriteFailed(f"Failed to write snapshot {dataset}: {str(exc)}") from exc

    def load_latest(self, dataset: str) -> dict[str, Any] | None:
        path = self.snapshot_dir / dataset / "latest.json"
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def read_latest(self, dataset: str) -> Optional[SnapshotEnvelope]:
        data = self.load_latest(dataset)
        if data is None:
            return None
        try:
            return SnapshotEnvelope(**data)
        except Exception as exc:
            logger.error("Failed to read snapshot %s: %s", dataset, exc)
            return None

    def check_freshness(self, dataset: str) -> FreshnessState:
        envelope = self.read_latest(dataset)
        if not envelope:
            return "missing"
        return "fresh"
