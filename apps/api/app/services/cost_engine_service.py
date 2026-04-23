import logging

from app.schemas.analysis import FxSimulationResult, LandedCostResult
from app.schemas.quote import ExtractedQuote
from app.schemas.reference import FreightRate, SupplierSeed, TariffRule

logger = logging.getLogger(__name__)


def compute_landed_cost(
    quote: ExtractedQuote,
    quantity_mt: float,
    fx_sim: FxSimulationResult,
    freight: FreightRate,
    tariff: TariffRule,
    supplier: SupplierSeed,
) -> LandedCostResult:
    """
    Calculate the total landed cost for a quote.
    """
    if quote.unit_price is None:
        raise ValueError("Quote must have a unit price")

    # a. material_cost = unit_price * quantity_mt (in quote currency)
    material_cost = quote.unit_price * quantity_mt

    # Get projected FX rates at the expected delivery day
    lead_days = quote.lead_time_days or 0
    # Cap index at horizon_days - 1
    fx_index = min(lead_days, fx_sim.horizon_days - 1)
    
    fx_p50 = fx_sim.p50_envelope[fx_index]
    fx_p10 = fx_sim.p10_envelope[fx_index]
    fx_p90 = fx_sim.p90_envelope[fx_index]

    # b. material_cost_myr_p50 = material_cost * fx_sim.p50
    material_cost_myr_p50 = round(material_cost * fx_p50, 2)
    # c. material_cost_myr_p10 = material_cost * fx_sim.p10
    material_cost_myr_p10 = round(material_cost * fx_p10, 2)
    # d. material_cost_myr_p90 = material_cost * fx_sim.p90
    material_cost_myr_p90 = round(material_cost * fx_p90, 2)

    # e. Freight anchors may be stored as per-container or per-MT values.
    current_spot = fx_sim.current_spot
    if freight.rate_unit.lower() == "mt":
        freight_base_cost = freight.rate_value * quantity_mt
    else:
        freight_base_cost = freight.rate_value * (quantity_mt / 20.0)
    freight_cost_myr = round(freight_base_cost * current_spot, 2)

    # f. tariff_cost_myr = material_cost_myr_p50 * tariff.tariff_rate_pct / 100
    tariff_cost_myr = round(material_cost_myr_p50 * (tariff.tariff_rate_pct / 100.0), 2)

    # g. moq_penalty = max(0, (quote.moq - quantity_mt) * unit_price * fx_rate) if moq > quantity
    moq_penalty = 0.0
    if quote.moq and quote.moq > quantity_mt:
        moq_penalty = round((quote.moq - quantity_mt) * quote.unit_price * fx_p50, 2)

    # h. supplier_trust_penalty = (1.0 - supplier.reliability_score) * material_cost_myr_p50 * 0.02
    trust_penalty = round((1.0 - supplier.reliability_score) * material_cost_myr_p50 * 0.02, 2)

    # i. total_landed_p50 = material + freight + tariff + moq_penalty + trust_penalty
    total_landed_p50 = round(
        material_cost_myr_p50 + freight_cost_myr + tariff_cost_myr + moq_penalty + trust_penalty,
        2,
    )
    
    # j. total_landed_p10 and p90 similarly
    total_landed_p10 = round(
        material_cost_myr_p10 + freight_cost_myr + tariff_cost_myr + moq_penalty + trust_penalty,
        2,
    )
    total_landed_p90 = round(
        material_cost_myr_p90 + freight_cost_myr + tariff_cost_myr + moq_penalty + trust_penalty,
        2,
    )

    return LandedCostResult(
        quote_id=str(quote.quote_id),
        material_cost_myr_p10=material_cost_myr_p10,
        material_cost_myr_p50=material_cost_myr_p50,
        material_cost_myr_p90=material_cost_myr_p90,
        freight_cost_myr=freight_cost_myr,
        tariff_cost_myr=tariff_cost_myr,
        moq_penalty=moq_penalty,
        trust_penalty=trust_penalty,
        total_landed_p10=total_landed_p10,
        total_landed_p50=total_landed_p50,
        total_landed_p90=total_landed_p90,
    )
