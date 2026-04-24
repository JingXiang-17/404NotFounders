from __future__ import annotations

from typing import Any

import httpx

from app.core.exceptions import ProviderError


class OpenDOSMProvider:
    BASE_URL = "https://api.data.gov.my/data-catalogue"

    async def fetch_dataset(self, dataset_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        return await self.fetch_json(self.BASE_URL, params={"id": dataset_id, "limit": limit})

    async def fetch_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            raise ProviderError(f"OpenDOSM request failed: {exc}") from exc

        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            data = payload.get("data") or payload.get("results")
            if isinstance(data, list):
                return data
        raise ProviderError("OpenDOSM response did not contain a JSON row list.")
