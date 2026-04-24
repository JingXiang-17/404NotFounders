from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.providers.sunsirs_provider import solve_hw_check_cookie
from app.repositories.raw_repository import RawRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.schemas.analysis import FxSimulationResult
from app.schemas.common import validate_resin_record
from app.schemas.quote import ExtractedQuote
from app.scrapers.sunsirs_pp_parser import parse_sunsirs_pp_rows
from app.services.resin_benchmark_service import ResinBenchmarkService, price_risk_label


class FakeSunSirsProvider:
    def __init__(self, html: str | None = None, fail: bool = False) -> None:
        self.html = html or _sample_html()
        self.fail = fail

    def fetch_pp_html(self, url: str) -> str:
        if self.fail:
            raise RuntimeError("network down")
        return self.html


def test_hw_check_solver_extracts_cookie() -> None:
    html = '<script>var _0x2 = "abc123def456"; document.cookie="HW_CHECK="+_0x2;</script>'
    assert solve_hw_check_cookie(html) == "abc123def456"


def test_sunsirs_parser_reads_all_pp_rows_and_infers_cny() -> None:
    records = parse_sunsirs_pp_rows(
        "| Commodity | Sectors | Price | Date | "
        "| PP | Rubber & plastics | 9,113.33 | 2026-04-24 | "
        "| PP | Rubber & plastics | 9123.33 | 2026-04-22 |"
    )

    assert len(records) == 2
    assert records[0]["price_value"] == pytest.approx(9113.33)
    assert records[0]["date_reference"] == "2026-04-24"
    assert records[0]["currency"] == "CNY"
    assert records[0]["unit"] == "CNY/MT"
    assert records[0]["currency_inferred"] is True


def test_resin_validator_accepts_cny_per_mt() -> None:
    validate_resin_record(parse_sunsirs_pp_rows("| PP | Rubber & plastics | 9113.33 | 2026-04-24 |")[0])


def test_price_risk_labels_cover_thresholds() -> None:
    assert price_risk_label(-10.0) == "below_market"
    assert price_risk_label(0.0) == "fair"
    assert price_risk_label(15.0) == "premium"
    assert price_risk_label(21.0) == "high_premium"


def test_resin_service_writes_snapshot_and_falls_back() -> None:
    temp_dir = _local_temp_dir()
    repository = SnapshotRepository(temp_dir / "snapshots")
    raw_repository = RawRepository(temp_dir / "raw")
    service = ResinBenchmarkService(
        provider=FakeSunSirsProvider(),
        raw_repository=raw_repository,
        snapshot_repository=repository,
    )

    try:
        envelope = service.refresh_sunsirs_snapshot()

        assert envelope.dataset == "resin"
        assert envelope.status == "success"
        assert envelope.record_count == 2

        failing_service = ResinBenchmarkService(
            provider=FakeSunSirsProvider(fail=True),
            raw_repository=raw_repository,
            snapshot_repository=repository,
        )
        fallback = failing_service.refresh_sunsirs_snapshot()

        assert fallback.status == "partial"
        assert fallback.data[0]["price_value"] == pytest.approx(9113.33)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_resin_service_merges_overlapping_scrape_windows() -> None:
    temp_dir = _local_temp_dir()
    repository = SnapshotRepository(temp_dir / "snapshots")
    raw_repository = RawRepository(temp_dir / "raw")

    try:
        first_service = ResinBenchmarkService(
            provider=FakeSunSirsProvider(
                _html_with_rows(
                    [
                        ("9113.33", "2026-04-24"),
                        ("9123.33", "2026-04-23"),
                        ("9183.33", "2026-04-22"),
                    ]
                )
            ),
            raw_repository=raw_repository,
            snapshot_repository=repository,
        )
        first_service.refresh_sunsirs_snapshot()

        second_service = ResinBenchmarkService(
            provider=FakeSunSirsProvider(
                _html_with_rows(
                    [
                        ("9100.00", "2026-04-25"),
                        ("9113.33", "2026-04-24"),
                        ("9120.00", "2026-04-23"),
                    ]
                )
            ),
            raw_repository=raw_repository,
            snapshot_repository=repository,
        )
        envelope = second_service.refresh_sunsirs_snapshot()

        dates = [record["date_reference"] for record in envelope.data]
        assert dates == ["2026-04-25", "2026-04-24", "2026-04-23", "2026-04-22"]
        assert envelope.record_count == 4
        assert envelope.data[2]["price_value"] == pytest.approx(9120.0)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_resin_ingest_route_returns_snapshot(monkeypatch) -> None:
    temp_dir = _local_temp_dir()
    service = ResinBenchmarkService(
        provider=FakeSunSirsProvider(),
        raw_repository=RawRepository(temp_dir / "raw"),
        snapshot_repository=SnapshotRepository(temp_dir / "snapshots"),
    )
    monkeypatch.setattr("app.api.routes.ingest_resin.build_default_resin_service", lambda: service)

    try:
        response = TestClient(app).post("/ingest/resin/sunsirs")

        assert response.status_code == 200
        payload = response.json()
        assert payload["dataset"] == "resin"
        assert payload["data"][0]["currency"] == "CNY"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_market_price_risk_uses_fx_to_compare_quotes() -> None:
    temp_dir = _local_temp_dir()
    service = ResinBenchmarkService(
        provider=FakeSunSirsProvider(),
        raw_repository=RawRepository(temp_dir / "raw"),
        snapshot_repository=SnapshotRepository(temp_dir / "snapshots"),
    )
    try:
        service.refresh_sunsirs_snapshot()

        quote = ExtractedQuote(
            quote_id="00000000-0000-0000-0000-000000000001",
            upload_id="00000000-0000-0000-0000-000000000002",
            supplier_name="Demo Supplier",
            unit_price=1400.0,
            currency="USD",
        )
        fx_sims = {
            "USDMYR": _fx("USDMYR", 4.7),
            "CNYMYR": _fx("CNYMYR", 0.65),
        }

        risks = service.build_market_price_risks([quote], fx_sims)

        assert risks[0]["risk_label"] == "premium"
        assert risks[0]["premium_pct"] > 10
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _fx(pair: str, rate: float) -> FxSimulationResult:
    return FxSimulationResult(
        pair=pair,
        current_spot=rate,
        implied_vol=0.05,
        p10_envelope=[rate] * 90,
        p50_envelope=[rate] * 90,
        p90_envelope=[rate] * 90,
        horizon_days=90,
    )


def _sample_html() -> str:
    return _html_with_rows([("9113.33", "2026-04-24"), ("9123.33", "2026-04-22")])


def _html_with_rows(rows: list[tuple[str, str]]) -> str:
    table_rows = "\n".join(
        f"<tr><td>PP</td><td>Rubber & plastics</td><td>{price}</td><td>{date}</td></tr>"
        for price, date in rows
    )
    return f"""
    <html><body>
      <table>
        <tr><th>Commodity</th><th>Sectors</th><th>Price</th><th>Date</th></tr>
        {table_rows}
      </table>
    </body></html>
    """


def _local_temp_dir() -> Path:
    path = Path("apps/api/tests/.tmp_resin") / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path
