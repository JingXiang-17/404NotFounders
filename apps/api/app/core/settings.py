from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_dotenv(*paths: Path) -> None:
    for path in paths:
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"").strip("'")
            os.environ.setdefault(key, value)


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _path_env(name: str, default: Path) -> Path:
    value = _optional_env(name)
    return Path(value) if value else default


@dataclass(frozen=True)
class AppSettings:
    root_dir: Path
    data_dir: Path
    reference_dir: Path
    snapshot_dir: Path
    raw_dir: Path
    tmp_dir: Path
    openweather_api_key: str | None = None
    gnews_api_key: str | None = None
    model_api_key: str | None = None

    @classmethod
    def from_env(cls) -> "AppSettings":
        root_dir = _repo_root()
        _load_dotenv(root_dir / "apps" / "api" / ".env", root_dir / ".env")
        data_dir = _path_env("DATA_DIR", root_dir / "data")
        reference_dir = _path_env("REFERENCE_DIR", data_dir / "reference")
        snapshot_dir = _path_env("SNAPSHOT_DIR", data_dir / "snapshots")
        raw_dir = _path_env("RAW_ARTIFACT_DIR", data_dir / "raw")
        tmp_dir = _path_env("TMP_DIR", data_dir / "tmp")
        return cls(
            root_dir=root_dir,
            data_dir=data_dir,
            reference_dir=reference_dir,
            snapshot_dir=snapshot_dir,
            raw_dir=raw_dir,
            tmp_dir=tmp_dir,
            openweather_api_key=_optional_env("OPENWEATHER_API_KEY"),
            gnews_api_key=_optional_env("GNEWS_API_KEY"),
            model_api_key=_optional_env("MODEL_API_KEY"),
        )
