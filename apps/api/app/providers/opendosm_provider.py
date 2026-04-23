from __future__ import annotations

import csv
import io
from urllib.request import urlopen

from app.core.exceptions import ProviderError


class OpenDOSMProvider:
    def fetch_csv(self, url: str) -> list[dict[str, str]]:
        try:
            with urlopen(url) as response:
                payload = response.read().decode("utf-8")
        except Exception as exc:  # pragma: no cover - network-facing guard
            raise ProviderError(f"OpenDOSM request failed: {exc}") from exc
        reader = csv.DictReader(io.StringIO(payload))
        return list(reader)

