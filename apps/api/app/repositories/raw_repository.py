import logging
import json
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

class RawRepository:
    def __init__(self, raw_dir: Path = settings.RAW_ARTIFACT_DIR):
        self.raw_dir = raw_dir
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def write_raw_artifact(self, dataset: str, data: Any, filename: str = None) -> None:
        if filename is None:
            filename = f"{dataset}_raw.json"
        filepath = self.raw_dir / filename
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                if isinstance(data, (dict, list)):
                    json.dump(data, f, indent=2)
                else:
                    f.write(str(data))
            logger.info(f"Raw artifact written: {filepath}")
        except Exception as e:
            logger.error(f"Failed to write raw artifact {filepath}: {e}")
