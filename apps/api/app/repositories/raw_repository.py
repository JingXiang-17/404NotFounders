from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.core.settings import AppSettings

logger = logging.getLogger(__name__)


class RawRepository:
    def __init__(self, raw_root: Any = None) -> None:
        if hasattr(raw_root, "raw_dir"):
            self.raw_dir = Path(raw_root.raw_dir)
        elif raw_root is None:
            self.raw_dir = Path(AppSettings.from_env().raw_dir)
        else:
            self.raw_dir = Path(raw_root)
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def write_text(self, dataset: str, filename: str, content: str) -> Path:
        target_dir = self.raw_dir / dataset
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / filename
        path.write_text(content, encoding="utf-8")
        return path

    def write_raw_artifact(self, dataset: str, data: Any, filename: str | None = None) -> Path:
        if filename is None:
            filename = f"{dataset}_raw.json"
        target_dir = self.raw_dir / dataset
        target_dir.mkdir(parents=True, exist_ok=True)
        filepath = target_dir / filename
        try:
            with filepath.open("w", encoding="utf-8") as handle:
                if isinstance(data, (dict, list)):
                    json.dump(data, handle, indent=2)
                else:
                    handle.write(str(data))
            logger.info("Raw artifact written: %s", filepath)
            return filepath
        except Exception as exc:
            logger.error("Failed to write raw artifact %s: %s", filepath, exc)
            raise
