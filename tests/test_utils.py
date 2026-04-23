from __future__ import annotations

import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
TMP_ROOT = ROOT / "data" / "tmp" / "test_runs"


@contextmanager
def workspace_temp_dir():
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    temp_dir = TMP_ROOT / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
