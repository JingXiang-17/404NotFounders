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


def _path_env(name: str, default: Path, *, base_dir: Path) -> Path:
    value = _optional_env(name)
    if not value:
        return default
    path = Path(value)
    return path if path.is_absolute() else (base_dir / path).resolve()


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
    model_base_url: str | None = None
    model_name: str | None = None
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str | None = None

    @classmethod
    def from_env(cls) -> "AppSettings":
        root_dir = _repo_root()
        api_dir = root_dir / "apps" / "api"
        _load_dotenv(api_dir / ".env", root_dir / ".env")
        data_dir = _path_env("DATA_DIR", root_dir / "data", base_dir=api_dir)
        reference_dir = _path_env("REFERENCE_DIR", data_dir / "reference", base_dir=api_dir)
        
        demo_mode_str = _optional_env("DEMO_MODE")
        demo_mode = demo_mode_str is not None and demo_mode_str.lower() in ("1", "true", "yes")
        
        snapshot_dir_name = "snapshots_frozen" if demo_mode else "snapshots"
        snapshot_dir = _path_env("SNAPSHOT_DIR", data_dir / snapshot_dir_name, base_dir=api_dir)
        raw_dir = _path_env("RAW_ARTIFACT_DIR", data_dir / "raw", base_dir=api_dir)
        tmp_dir = _path_env("TMP_DIR", data_dir / "tmp", base_dir=api_dir)
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
            model_base_url=_optional_env("MODEL_BASE_URL"),
            model_name=_optional_env("MODEL_NAME"),
            langfuse_public_key=_optional_env("LANGFUSE_PUBLIC_KEY"),
            langfuse_secret_key=_optional_env("LANGFUSE_SECRET_KEY"),
            langfuse_host=_optional_env("LANGFUSE_HOST"),
        )
        instance.validate_langfuse()
        return instance

    def validate_langfuse(self) -> None:
        """Raise RuntimeError at startup if any Langfuse credential is missing."""
        missing: list[str] = []
        if not self.langfuse_public_key:
            missing.append("LANGFUSE_PUBLIC_KEY")
        if not self.langfuse_secret_key:
            missing.append("LANGFUSE_SECRET_KEY")
        if not self.langfuse_host:
            missing.append("LANGFUSE_HOST")
        if missing:
            raise RuntimeError(
                f"[LintasNiaga] Langfuse is required but the following environment variables are "
                f"not set: {', '.join(missing)}. "
                f"Add them to apps/api/.env before starting the server."
            )
