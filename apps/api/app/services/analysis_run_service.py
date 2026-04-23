import logging
import uuid
from typing import Dict, List, Tuple
from uuid import UUID

from app.core.constants import SUPPORTED_HS_CODE, SUPPORTED_IMPORT_COUNTRY
from app.core.exceptions import NoValidQuotes
from app.schemas.analysis import (
    AnalysisResultPayload,
    FxSimulationResult,
    LandedCostResult,
    RankedQuote,
    RankedQuoteDetail,
    RecommendationCard,
)
from app.schemas.quote import ExtractedQuote
from app.schemas.reference import FreightRate, SupplierSeed, TariffRule
from app.services.ai_orchestrator_service import (
    OrchestratorState,
    build_ai_graph,
    get_reasoning_system_prompt,
)
from app.services.context_builder_service import build_ai_context
from app.services.cost_engine_service import compute_landed_cost
from app.services.fx_service import simulate_fx_paths
from app.services.quote_ingest_service import get_quote_state
from app.services.recommendation_assembler_service import assemble_recommendation
from app.services.recommendation_engine_service import rank_quotes
from app.services.reference_data_service import load_all_reference_data

logger = logging.getLogger(__name__)

_run_contexts: Dict[str, str] = {}
_run_results: Dict[str, AnalysisResultPayload] = {}

PORT_KEYWORDS = {
    "CNNGB": {"ningbo", "zhejiang", "beilun"},
    "CNSZX": {"shenzhen", "yantian"},
    "THBKK": {"bangkok", "laem chabang"},
    "IDJKT": {"jakarta", "tanjung priok"},
}
COUNTRY_TO_DEFAULT_PORT = {
    "CN": "CNNGB",
    "TH": "THBKK",
    "ID": "IDJKT",
}
COUNTRY_KEYWORDS = {
    "CN": {"china", "ningbo", "shenzhen", "zhejiang", "yantian"},
    "TH": {"thailand", "bangkok", "laem chabang"},
    "ID": {"indonesia", "jakarta", "tanjung priok"},
}


def _infer_origin_country(origin_port_or_country: str | None) -> str | None:
    if not origin_port_or_country:
        return None
    normalized = origin_port_or_country.strip().lower()
    for country_code, keywords in COUNTRY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return country_code
    return None


def _infer_origin_port_code(origin_port_or_country: str | None, origin_country: str | None) -> str | None:
    if origin_port_or_country:
        normalized = origin_port_or_country.strip().lower()
        for port_code, keywords in PORT_KEYWORDS.items():
            if any(keyword in normalized for keyword in keywords):
                return port_code
    if origin_country:
        return COUNTRY_TO_DEFAULT_PORT.get(origin_country)
    return None


def _match_supplier_seed(quote: ExtractedQuote, supplier_seeds: list[SupplierSeed]) -> SupplierSeed | None:
    if quote.supplier_name:
        normalized_supplier = quote.supplier_name.strip().lower()
        exact_match = next(
            (seed for seed in supplier_seeds if seed.supplier_name.strip().lower() == normalized_supplier),
            None,
        )
        if exact_match:
            return exact_match
        fuzzy_match = next(
            (
                seed
                for seed in supplier_seeds
                if seed.supplier_name.strip().lower() in normalized_supplier
                or normalized_supplier in seed.supplier_name.strip().lower()
            ),
            None,
        )
        if fuzzy_match:
            return fuzzy_match

    origin_country = _infer_origin_country(quote.origin_port_or_country)
    if origin_country:
        candidates = [seed for seed in supplier_seeds if seed.country_code == origin_country]
        if candidates:
            return min(
                candidates,
                key=lambda seed: abs(seed.typical_lead_days - (quote.lead_time_days or seed.typical_lead_days)),
            )
    return None


def _match_freight_rate(
    quote: ExtractedQuote,
    freight_rates: list[FreightRate],
    supplier_seed: SupplierSeed | None,
) -> FreightRate | None:
    origin_country = _infer_origin_country(quote.origin_port_or_country) or (
        supplier_seed.country_code if supplier_seed else None
    )
    origin_port = _infer_origin_port_code(quote.origin_port_or_country, origin_country)

    for rate in freight_rates:
        if origin_country and rate.origin_country != origin_country:
            continue
        if origin_port and rate.origin_port != origin_port:
            continue
        return rate

    if origin_country:
        return next((rate for rate in freight_rates if rate.origin_country == origin_country), None)
    return None


def _match_tariff_rule(tariffs: list[TariffRule]) -> TariffRule:
    return next(
        tariff
        for tariff in tariffs
        if tariff.hs_code == SUPPORTED_HS_CODE and tariff.import_country == SUPPORTED_IMPORT_COUNTRY
    )


def _fallback_fx_simulation(pair: str, currency: str) -> FxSimulationResult:
    if currency == "USD":
        current_spot = 4.7
        p10 = 4.6
        p50 = 4.7
        p90 = 4.8
    elif currency == "CNY":
        current_spot = 0.65
        p10 = 0.63
        p50 = 0.65
        p90 = 0.67
    elif currency == "THB":
        current_spot = 0.13
        p10 = 0.125
        p50 = 0.13
        p90 = 0.135
    else:
        current_spot = 0.00014
        p10 = 0.00013
        p50 = 0.00014
        p90 = 0.00015
    return FxSimulationResult(
        pair=pair,
        current_spot=current_spot,
        implied_vol=0.05,
        p10_envelope=[p10] * 90,
        p50_envelope=[p50] * 90,
        p90_envelope=[p90] * 90,
        horizon_days=90,
    )


async def execute_analysis_run(
    extracted_quotes: List[ExtractedQuote],
    quantity_mt: float,
    urgency: str,
    hedge_preference: str,
) -> Tuple[str, RecommendationCard]:
    run_id = str(uuid.uuid4())
    logger.info("Starting analysis run %s for %s quotes.", run_id, len(extracted_quotes))

    reference_data = load_all_reference_data()
    freight_rates = reference_data["freight_rates"]
    tariffs = reference_data["tariffs"]
    supplier_seeds = reference_data["supplier_seeds"]
    tariff_rule = _match_tariff_rule(tariffs)

    currencies = {q.currency for q in extracted_quotes if q.currency and q.currency != "MYR"}
    fx_sims: Dict[str, FxSimulationResult] = {}
    for curr in currencies:
        pair = f"{curr}MYR"
        try:
            fx_sims[pair] = simulate_fx_paths(pair=pair)
        except Exception as exc:
            logger.warning("Failed to simulate %s: %s", pair, exc)
            fx_sims[pair] = _fallback_fx_simulation(pair, curr)

    costs: List[LandedCostResult] = []
    quote_lookup: Dict[str, ExtractedQuote] = {}
    reliability_lookup: Dict[str, float] = {}
    for quote in extracted_quotes:
        pair = f"{quote.currency}MYR"
        fx_sim = fx_sims.get(pair)
        try:
            if fx_sim is None:
                raise ValueError(f"Missing FX simulation for {pair}")
            supplier_seed = _match_supplier_seed(quote, supplier_seeds)
            if supplier_seed is None:
                raise ValueError(f"No supplier seed match for quote {quote.quote_id}")
            freight_rate = _match_freight_rate(quote, freight_rates, supplier_seed)
            if freight_rate is None:
                raise ValueError(f"No freight rate match for quote {quote.quote_id}")
            costs.append(
                compute_landed_cost(
                    quote=quote,
                    quantity_mt=quantity_mt,
                    fx_sim=fx_sim,
                    freight=freight_rate,
                    tariff=tariff_rule,
                    supplier=supplier_seed,
                )
            )
            quote_lookup[str(quote.quote_id)] = quote
            reliability_lookup[str(quote.quote_id)] = supplier_seed.reliability_score
        except Exception as exc:
            logger.error("Failed to compute cost for quote %s: %s", quote.quote_id, exc)

    if not costs:
        raise ValueError("No valid costs could be computed from the provided quotes.")

    ranked_quotes = rank_quotes(costs)
    single_quote_mode = len(ranked_quotes) == 1

    context_str = build_ai_context(
        ranked_quotes=ranked_quotes,
        costs=costs,
        fx_sims=fx_sims,
        macro_snapshot=None,
        urgency=urgency,
        hedge_preference=hedge_preference,
    )
    _run_contexts[run_id] = context_str

    try:
        graph = build_ai_graph()
        initial_state: OrchestratorState = {
            "context_str": context_str,
            "system_prompt": get_reasoning_system_prompt(single_quote_mode=single_quote_mode),
            "ai_json_output": {},
            "messages": [],
        }
        final_state = await graph.ainvoke(initial_state)
        ai_json = final_state.get("ai_json_output", {})
    except Exception as exc:
        logger.error("AI orchestration failed: %s", exc)
        ai_json = {}

    recommendation = assemble_recommendation(
        ranked_quotes=ranked_quotes,
        ai_json=ai_json,
        single_quote_mode=single_quote_mode,
    )
    ranked_quote_details = [
        RankedQuoteDetail(
            rank=ranked_quote.rank,
            delta_vs_winner=ranked_quote.delta_vs_winner,
            quote=quote_lookup[str(ranked_quote.cost_result.quote_id)],
            cost_result=ranked_quote.cost_result,
            reliability_score=reliability_lookup.get(str(ranked_quote.cost_result.quote_id)),
        )
        for ranked_quote in ranked_quotes
        if str(ranked_quote.cost_result.quote_id) in quote_lookup
    ]
    _run_results[run_id] = AnalysisResultPayload(
        run_id=run_id,
        recommendation=recommendation,
        ranked_quotes=ranked_quote_details,
        fx_simulations=fx_sims,
        trace_url=None,
    )
    return run_id, recommendation


async def run_analysis(
    quote_ids: List[str],
    quantity_mt: float,
    urgency: str,
    hedge_preference: str,
) -> Tuple[str, RecommendationCard]:
    valid_quotes: List[ExtractedQuote] = []
    for raw_quote_id in quote_ids:
        try:
            quote_id = UUID(raw_quote_id)
        except ValueError:
            logger.warning("Skipping malformed quote id: %s", raw_quote_id)
            continue
        state = get_quote_state(quote_id)
        if state is None or state.extracted_quote is None or state.validation is None:
            logger.warning("Skipping missing quote state for id: %s", raw_quote_id)
            continue
        if state.validation.status != "valid":
            logger.warning("Skipping non-valid quote %s with status %s", raw_quote_id, state.validation.status)
            continue
        valid_quotes.append(state.extracted_quote)

    if not valid_quotes:
        raise NoValidQuotes("No valid uploaded quotes were found for analysis.")

    return await execute_analysis_run(
        extracted_quotes=valid_quotes,
        quantity_mt=quantity_mt,
        urgency=urgency,
        hedge_preference=hedge_preference,
    )


def get_context_for_run(run_id: str) -> str:
    return _run_contexts.get(run_id, "")


def get_result_for_run(run_id: str) -> AnalysisResultPayload | None:
    return _run_results.get(run_id)
