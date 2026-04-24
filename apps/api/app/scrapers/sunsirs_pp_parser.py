from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

try:
    import trafilatura  # type: ignore
except ImportError:  # pragma: no cover - runtime fallback
    trafilatura = None

from app.core.exceptions import ProviderError
from app.providers.sunsirs_provider import SUNSIRS_PP_URL

PP_ROW_PATTERN = re.compile(
    r"\|\s*PP\s*\|\s*([^|]*)\|\s*([0-9][0-9,]*(?:\.\d{1,2})?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|",
    re.IGNORECASE,
)
PP_BLOCK_PATTERN = re.compile(
    r"(?:^|\n)\s*PP\s*\n\s*([^\n]+?)\s*\n\s*([0-9][0-9,]*(?:\.\d{1,2})?)\s*\n\s*(\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedSunSirsRow:
    sector: str
    price: float
    observation_date: str
    evidence_snippet: str


def extract_sunsirs_pp_text(html: str) -> tuple[str, str]:
    if trafilatura is not None:
        text = trafilatura.extract(html, include_links=False, include_tables=True)
        if text and "PP" in text and re.search(r"\d{4}-\d{2}-\d{2}", text):
            return text, "trafilatura_tables"

    table_text = _extract_table_text(html)
    if table_text:
        return table_text, "html_table"

    selector_text = _extract_selector_text(html)
    if selector_text:
        return selector_text, "html_selectors"

    raise ProviderError("SunSirs PP page did not contain extractable PP table text.")


def parse_sunsirs_pp_rows(text: str, *, source_url: str = SUNSIRS_PP_URL) -> list[dict[str, Any]]:
    rows: list[ParsedSunSirsRow] = []
    seen: set[tuple[str, float]] = set()
    for match in PP_ROW_PATTERN.finditer(text):
        sector = _clean(match.group(1)) or "Rubber & plastics"
        price = float(match.group(2).replace(",", ""))
        observation_date = match.group(3)
        _append_row(rows, seen, sector, price, observation_date, _clean(match.group(0)))

    for match in PP_BLOCK_PATTERN.finditer(text):
        sector = _clean(match.group(1)) or "Rubber & plastics"
        price = float(match.group(2).replace(",", ""))
        observation_date = match.group(3)
        evidence = f"| PP | {sector} | {price:.2f} | {observation_date} |"
        _append_row(rows, seen, sector, price, observation_date, evidence)

    if not rows:
        raise ProviderError("SunSirs PP table parser did not find any PP price rows.")

    rows.sort(key=lambda item: item.observation_date, reverse=True)
    return [_row_to_record(row, source_url=source_url) for row in rows]


def _append_row(
    rows: list[ParsedSunSirsRow],
    seen: set[tuple[str, float]],
    sector: str,
    price: float,
    observation_date: str,
    evidence_snippet: str,
) -> None:
    key = (observation_date, price)
    if key in seen:
        return
    seen.add(key)
    rows.append(
        ParsedSunSirsRow(
            sector=sector,
            price=price,
            observation_date=observation_date,
            evidence_snippet=evidence_snippet,
        )
    )


def _row_to_record(row: ParsedSunSirsRow, *, source_url: str) -> dict[str, Any]:
    datetime.strptime(row.observation_date, "%Y-%m-%d")
    return {
        "series_key": "sunsirs.pp.wire_drawing.cn",
        "commodity": "PP wire-drawing benchmark",
        "region": "China",
        "sector": row.sector,
        "price_value": row.price,
        "currency": "CNY",
        "unit": "CNY/MT",
        "date_reference": row.observation_date,
        "confidence": 1.0,
        "parser_confidence": "high",
        "confidence_reason": "parsed from SunSirs PP commodity table row",
        "currency_inferred": True,
        "currency_inference_reason": "SunSirs China PP spot price page labels unit RMB/ton; normalized to CNY/MT.",
        "evidence_snippet": row.evidence_snippet,
        "source_name": "SunSirs",
        "source_url": source_url,
    }


def _extract_table_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    lines: list[str] = []
    for tr in soup.select("tr"):
        cells = [_clean(cell.get_text(" ", strip=True)) for cell in tr.find_all(["th", "td"])]
        cells = [cell for cell in cells if cell]
        if len(cells) >= 4:
            lines.append("| " + " | ".join(cells[:4]) + " |")
    return " ".join(lines)


def _extract_selector_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    selectors = [
        "div.article-content",
        "div.news-content",
        "div.content",
        "div.detail-content",
        "div.detail",
        "article",
    ]
    for selector in selectors:
        element = soup.select_one(selector)
        if not element:
            continue
        text = _clean(element.get_text(" ", strip=True))
        if "PP" in text and re.search(r"\d{4}-\d{2}-\d{2}", text):
            return text
    return ""


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
