import uuid
from datetime import date

from app.schemas.analysis import FxSimulationResult
from app.schemas.quote import ExtractedQuote
from app.schemas.reference import FreightRate, SupplierSeed, TariffRule
from app.services.cost_engine_service import compute_landed_cost


def test_compute_landed_cost():
    quote_id = uuid.uuid4()
    upload_id = uuid.uuid4()
    
    quote = ExtractedQuote(
        quote_id=quote_id,
        upload_id=upload_id,
        supplier_name="Test Supplier",
        unit_price=1000.0,
        currency="USD",
        moq=30,
        lead_time_days=45,
    )
    
    fx_sim = FxSimulationResult(
        pair="USDMYR",
        current_spot=4.5,
        implied_vol=0.1,
        p10_envelope=[4.0] * 90,
        p50_envelope=[4.5] * 90,
        p90_envelope=[5.0] * 90,
        horizon_days=90,
    )
    
    freight = FreightRate(
        origin_country="CN",
        origin_port="CNSHA",
        destination_port="MYPKG",
        incoterm="FOB",
        currency="USD",
        rate_value=500.0,
        rate_unit="container",
        valid_from=date(2024, 1, 1),
        valid_to=date(2024, 12, 31),
        source_note="Test",
    )
    
    tariff = TariffRule(
        hs_code="3902.10",
        product_name="PP Resin",
        import_country="MY",
        tariff_rate_pct=10.0,
        tariff_type="import",
        source_note="Test",
    )
    
    supplier = SupplierSeed(
        supplier_name="Test Supplier",
        country_code="CN",
        port="CNSHA",
        reliability_score=0.9,
        typical_lead_days=45,
        notes="Test",
    )
    
    quantity_mt = 20.0
    
    result = compute_landed_cost(
        quote=quote,
        quantity_mt=quantity_mt,
        fx_sim=fx_sim,
        freight=freight,
        tariff=tariff,
        supplier=supplier,
    )
    
    # Material Cost checks
    # price (1000) * qty (20) = 20000 USD
    # P50 FX is 4.5 -> 90000 MYR
    assert result.material_cost_myr_p50 == 90000.0
    assert result.material_cost_myr_p10 == 80000.0
    assert result.material_cost_myr_p90 == 100000.0
    
    # Freight Cost checks
    # rate (500) * (20 / 20) = 500 USD
    # spot FX is 4.5 -> 2250 MYR
    assert result.freight_cost_myr == 2250.0
    
    # Tariff Cost checks
    # material_cost_myr_p50 (90000) * 10% = 9000 MYR
    assert result.tariff_cost_myr == 9000.0
    
    # MOQ penalty checks
    # qty = 20, MOQ = 30 -> penalty applies on 10 units at P50 FX
    # 10 * 1000 * 4.5 = 45000 MYR
    assert result.moq_penalty == 45000.0
    
    # Trust penalty checks
    # reliability 0.9 -> 0.1 * material_cost_myr_p50 * 0.02 = 0.1 * 90000 * 0.02 = 180.0
    assert result.trust_penalty == 180.0
    
    # Total landed cost P50
    # 90000 + 2250 + 9000 + 45000 + 180 = 146430
    assert result.total_landed_p50 == 146430.0
