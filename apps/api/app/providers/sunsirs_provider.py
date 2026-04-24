from __future__ import annotations

import logging
import re
import time

import httpx

from app.core.exceptions import ProviderError

logger = logging.getLogger(__name__)

SUNSIRS_PP_URL = "https://www.sunsirs.com/uk/prodetail-718.html"
HTTP_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class SunSirsProvider:
    def __init__(self, *, timeout_seconds: float = 30.0, max_retries: int = 3) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def fetch_pp_html(self, url: str = SUNSIRS_PP_URL) -> str:
        try:
            with self._create_client() as client:
                return self._fetch_with_challenge(client, url)
        except Exception as exc:
            raise ProviderError(f"SunSirs PP page fetch failed: {exc}") from exc

    def _create_client(self) -> httpx.Client:
        return httpx.Client(
            headers={
                "User-Agent": HTTP_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
            timeout=self.timeout_seconds,
            follow_redirects=True,
        )

    def _fetch_with_challenge(self, client: httpx.Client, url: str) -> str:
        for attempt in range(1, self.max_retries + 1):
            response = client.get(url)
            response.raise_for_status()
            html = response.text
            if not is_hw_check_page(html):
                return html

            cookie_value = solve_hw_check_cookie(html)
            if not cookie_value:
                logger.warning("SunSirs HW_CHECK challenge was present but cookie could not be parsed.")
                continue

            client.cookies.set("HW_CHECK", cookie_value, domain="www.sunsirs.com", path="/")
            time.sleep(0.8)
            response = client.get(url)
            response.raise_for_status()
            html = response.text
            if not is_hw_check_page(html):
                return html
            logger.warning("SunSirs HW_CHECK cookie did not clear challenge on attempt %d.", attempt)

        raise ProviderError(f"SunSirs challenge could not be cleared after {self.max_retries} attempts.")


def solve_hw_check_cookie(html: str) -> str | None:
    match = re.search(r'var\s+_0x2\s*=\s*"([a-fA-F0-9]+)"', html)
    return match.group(1) if match else None


def is_hw_check_page(html: str) -> bool:
    return "HW_CHECK" in html or "正在进行安全检查" in html
