from datetime import date
from uuid import uuid4

from app.schemas.analysis import FxSimulationResult, LandedCostResult
from app.schemas.quote import ExtractedQuote
from app.schemas.reference import FreightRate, SupplierSeed, TariffRule
from app.services.landed_cost_monte_carlo_service import (
    LandedCostMonteCarloService,
    MonteCarloQuoteInput,
)


class _EmptySnapshotRepository:
    def read_latest(self, dataset: str):
        return None


def _quote_input() -> MonteCarloQuoteInput:
    quote_id = uuid4()
    quote = ExtractedQuote(
        quote_id=quote_id,
        upload_id=uuid4(),
        supplier_name="Sinopec Ind.",
        origin_port_or_country="China Ningbo",
        incoterm="FOB",
        unit_price=840.0,
        currency="USD",
        moq=80,
        lead_time_days=21,
        payment_terms="30 days",
    )
    cost = LandedCostResult(
        quote_id=str(quote_id),
        material_cost_myr_p10=386400.0,
        material_cost_myr_p50=394800.0,
        material_cost_myr_p90=403200.0,
        freight_cost_myr=11750.0,
        tariff_cost_myr=19740.0,
        moq_penalty=0.0,
        trust_penalty=1579.2,
        total_landed_p10=419469.2,
        total_landed_p50=427869.2,
        total_landed_p90=436269.2,
    )
    fx = FxSimulationResult(
        pair="USDMYR",
        current_spot=4.7,
        implied_vol=0.08,
        p10_envelope=[4.6] * 90,
        p50_envelope=[4.7] * 90,
        p90_envelope=[4.8] * 90,
        horizon_days=90,
    )
    freight = FreightRate(
        origin_country="CN",
        origin_port="CNNGB",
        destination_port="MYPKG",
        incoterm="FOB",
        currency="USD",
        rate_value=2500.0,
        rate_unit="container",
        valid_from=date(2026, 1, 1),
        valid_to=date(2026, 12, 31),
        source_note="test",
    )
    tariff = TariffRule(
        hs_code="3902.10",
        product_name="PP Resin",
        import_country="MY",
        tariff_rate_pct=5.0,
        tariff_type="ad_valorem",
        source_note="test",
    )
    supplier = SupplierSeed(
        supplier_name="Sinopec Ind.",
        country_code="CN",
        port="CNNGB",
        reliability_score=0.8,
        typical_lead_days=21,
        notes="test",
    )
    return MonteCarloQuoteInput(
        quote=quote,
        cost_result=cost,
        fx_sim=fx,
        freight=freight,
        tariff=tariff,
        supplier=supplier,
    )


def test_monte_carlo_is_deterministic_for_same_run_and_quote():
    service = LandedCostMonteCarloService(snapshot_repository=_EmptySnapshotRepository(), n_paths=500)
    quote_input = _quote_input()
    breakdown = service.build_risk_driver_breakdown(
        macro_context={},
        top_news=[],
        port_risks=[],
        resin_price_scenario=None,
        tariff_rate_pct=5.0,
    )

    first = service.simulate_quote(
        run_id="run-123",
        quote_input=quote_input,
        quantity_mt=100,
        hedge_ratio=50,
        risk_driver_breakdown=breakdown,
        resin_price_scenario=None,
    )
    second = service.simulate_quote(
        run_id="run-123",
        quote_input=quote_input,
        quantity_mt=100,
        hedge_ratio=50,
        risk_driver_breakdown=breakdown,
        resin_price_scenario=None,
    )

    assert first.p10_envelope == second.p10_envelope
    assert first.p50_envelope == second.p50_envelope
    assert first.p90_envelope == second.p90_envelope


def test_hedge_narrows_fx_risk_without_zeroing_non_fx_risk():
    service = LandedCostMonteCarloService(snapshot_repository=_EmptySnapshotRepository(), n_paths=500)
    quote_input = _quote_input()
    breakdown = service.build_risk_driver_breakdown(
        macro_context={"trade": {"status": "DANGER"}},
        top_news=[{"category": "finance", "relevance_score": 1.0}],
        port_risks=[{"max_risk_score": 65}],
        resin_price_scenario=None,
        tariff_rate_pct=5.0,
    )

    unhedged = service.simulate_quote(
        run_id="run-456",
        quote_input=quote_input,
        quantity_mt=100,
        hedge_ratio=0,
        risk_driver_breakdown=breakdown,
        resin_price_scenario=None,
    )
    fully_hedged = service.simulate_quote(
        run_id="run-456",
        quote_input=quote_input,
        quantity_mt=100,
        hedge_ratio=100,
        risk_driver_breakdown=breakdown,
        resin_price_scenario=None,
    )

    assert fully_hedged.risk_width_envelope[-1] < unhedged.risk_width_envelope[-1]
    assert fully_hedged.risk_width_envelope[-1] > 0


def test_risk_driver_normalizers_are_bounded_with_missing_snapshots():
    service = LandedCostMonteCarloService(snapshot_repository=_EmptySnapshotRepository(), n_paths=100)
    breakdown = service.build_risk_driver_breakdown(
        macro_context={},
        top_news=[],
        port_risks=[],
        resin_price_scenario=None,
        tariff_rate_pct=5.0,
    )
    values = breakdown.model_dump(exclude={"notes"}).values()

    assert all(0.0 <= value <= 1.0 for value in values)
    assert "weather" in breakdown.notes
    assert "resin" in breakdown.notes
