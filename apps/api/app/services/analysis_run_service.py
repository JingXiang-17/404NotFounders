import logging
import json
import uuid
from datetime import UTC, datetime
from typing import Dict, List, Tuple
from uuid import UUID

from app.core.constants import SUPPORTED_HS_CODE, SUPPORTED_IMPORT_COUNTRY
from app.core.exceptions import NoValidQuotes
from app.schemas.analysis import (
    AnalysisResultPayload,
    BankInstructionDraft,
    FxSimulationResult,
    HedgeScenarioResult,
    LandedCostResult,
    LandedCostScenario,
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
from app.services.landed_cost_monte_carlo_service import (
    LandedCostMonteCarloService,
    MonteCarloQuoteInput,
)
from app.providers.llm_provider import build_llm_provider
from app.services.quote_ingest_service import get_quote_state
from app.services.recommendation_assembler_service import assemble_recommendation
from app.services.recommendation_engine_service import rank_quotes
from app.services.reference_data_service import load_all_reference_data
from app.services.macro_data_service import build_default_macro_service
from app.services.news_event_service import build_default_news_service
from app.services.resin_benchmark_service import build_default_resin_service
from app.services.weather_risk_service import build_default_weather_service

logger = logging.getLogger(__name__)

_run_contexts: Dict[str, str] = {}
_run_results: Dict[str, AnalysisResultPayload] = {}
_run_monte_carlo_inputs: Dict[str, dict] = {}

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
    monte_carlo_inputs: list[MonteCarloQuoteInput] = []
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
            cost_result = compute_landed_cost(
                quote=quote,
                quantity_mt=quantity_mt,
                fx_sim=fx_sim,
                freight=freight_rate,
                tariff=tariff_rule,
                supplier=supplier_seed,
            )
            costs.append(cost_result)
            monte_carlo_inputs.append(
                MonteCarloQuoteInput(
                    quote=quote,
                    cost_result=cost_result,
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

    # Pull live context from snapshots (read-only — never scrapes live)
    macro_svc = build_default_macro_service()
    news_svc = build_default_news_service()
    resin_svc = build_default_resin_service()
    weather_svc = build_default_weather_service()

    macro_context = macro_svc.get_macro_context_for_ai()
    top_news = news_svc.get_top_events_for_context(top_n=5)
    resin_benchmark = resin_svc.get_latest_benchmark_for_context()
    market_price_risks = resin_svc.build_market_price_risks(list(quote_lookup.values()), fx_sims)
    resin_price_scenario = resin_svc.build_price_scenario()
    port_risks = weather_svc.get_port_risk_for_context()
    risk_by_quote_id = {risk["quote_id"]: risk for risk in market_price_risks}
    mc_service = LandedCostMonteCarloService()
    risk_driver_breakdown = mc_service.build_risk_driver_breakdown(
        macro_context=macro_context,
        top_news=top_news,
        port_risks=port_risks,
        resin_price_scenario=resin_price_scenario,
        tariff_rate_pct=tariff_rule.tariff_rate_pct,
    )
    ai_context_scenarios = mc_service.build_scenarios(
        run_id=run_id,
        quote_inputs=monte_carlo_inputs,
        quantity_mt=quantity_mt,
        hedge_ratio=0.0,
        risk_driver_breakdown=risk_driver_breakdown,
        resin_price_scenario=resin_price_scenario,
    )
    ai_context_winner_id = str(ranked_quotes[0].cost_result.quote_id)
    ai_context_selected_scenario = ai_context_scenarios.get(ai_context_winner_id)

    # Merge everything into macro_snapshot dict for context builder
    combined_snapshot: dict = {}
    if macro_context:
        combined_snapshot["macro"] = macro_context
    if top_news:
        combined_snapshot["news_events"] = top_news
    if resin_benchmark:
        combined_snapshot["resin_benchmark"] = resin_benchmark
    if market_price_risks:
        combined_snapshot["market_price_risks"] = market_price_risks
    if resin_price_scenario:
        combined_snapshot["resin_price_scenario"] = resin_price_scenario
    if port_risks:
        combined_snapshot["port_weather_risk"] = port_risks
    combined_snapshot["risk_driver_breakdown"] = risk_driver_breakdown.model_dump(mode="json")
    if ai_context_selected_scenario:
        combined_snapshot["landed_cost_monte_carlo"] = {
            "selected_quote_id": ai_context_winner_id,
            "method": ai_context_selected_scenario.method,
            "p50_day0": ai_context_selected_scenario.p50_envelope[0],
            "p50_day30": ai_context_selected_scenario.p50_envelope[-1],
            "p90_day30": ai_context_selected_scenario.p90_envelope[-1],
            "direction": _fan_chart_direction(ai_context_selected_scenario),
            "buy_later_signal": _fan_chart_direction(ai_context_selected_scenario) == "down",
            "instruction": (
                "If direction is down and urgency allows, recommend waiting, requoting, or staging the order. "
                "If direction is up or P90 tail risk is high, recommend locking supplier/FX exposure sooner."
            ),
        }

    context_str = build_ai_context(
        ranked_quotes=ranked_quotes,
        costs=costs,
        fx_sims=fx_sims,
        macro_snapshot=combined_snapshot if combined_snapshot else None,
        urgency=urgency,
        hedge_preference=hedge_preference,
    )
    _run_contexts[run_id] = context_str

    # No try/except — AI orchestration failures must propagate so the caller
    # receives a proper error response rather than a silent empty recommendation.
    graph = build_ai_graph()
    initial_state: OrchestratorState = {
        "context_str": context_str,
        "system_prompt": get_reasoning_system_prompt(single_quote_mode=single_quote_mode),
        "ai_json_output": {},
        "messages": [],
        "trace_url": None,
    }
    final_state = await graph.ainvoke(initial_state)
    ai_json = final_state.get("ai_json_output", {})
    trace_url = final_state.get("trace_url")

    recommendation = assemble_recommendation(
        ranked_quotes=ranked_quotes,
        ai_json=ai_json,
        single_quote_mode=single_quote_mode,
    )
    scenario_by_quote = mc_service.build_scenarios(
        run_id=run_id,
        quote_inputs=monte_carlo_inputs,
        quantity_mt=quantity_mt,
        hedge_ratio=recommendation.hedge_pct,
        risk_driver_breakdown=risk_driver_breakdown,
        resin_price_scenario=resin_price_scenario,
    )
    unhedged_scenario_by_quote = mc_service.build_scenarios(
        run_id=run_id,
        quote_inputs=monte_carlo_inputs,
        quantity_mt=quantity_mt,
        hedge_ratio=0.0,
        risk_driver_breakdown=risk_driver_breakdown,
        resin_price_scenario=resin_price_scenario,
    )
    winner_quote_id = str(ranked_quotes[0].cost_result.quote_id)
    selected_scenario = scenario_by_quote.get(winner_quote_id)
    hedge_simulation = (
        mc_service.to_hedge_result(
            scenario=selected_scenario,
            unhedged_scenario=unhedged_scenario_by_quote.get(winner_quote_id),
        )
        if selected_scenario
        else None
    )

    ranked_quote_details = [
        RankedQuoteDetail(
            rank=ranked_quote.rank,
            delta_vs_winner=ranked_quote.delta_vs_winner,
            quote=quote_lookup[str(ranked_quote.cost_result.quote_id)],
            cost_result=ranked_quote.cost_result,
            reliability_score=reliability_lookup.get(str(ranked_quote.cost_result.quote_id)),
            market_price_risk=risk_by_quote_id.get(str(ranked_quote.cost_result.quote_id)),
        )
        for ranked_quote in ranked_quotes
        if str(ranked_quote.cost_result.quote_id) in quote_lookup
    ]
    _run_monte_carlo_inputs[run_id] = {
        "quote_inputs": monte_carlo_inputs,
        "quantity_mt": quantity_mt,
        "risk_driver_breakdown": risk_driver_breakdown,
        "resin_price_scenario": resin_price_scenario,
        "winner_quote_id": winner_quote_id,
    }
    _run_results[run_id] = AnalysisResultPayload(
        run_id=run_id,
        recommendation=recommendation,
        ranked_quotes=ranked_quote_details,
        fx_simulations=fx_sims,
        resin_benchmark=resin_benchmark,
        market_price_risks=market_price_risks,
        resin_price_scenario=resin_price_scenario,
        landed_cost_scenarios=scenario_by_quote,
        selected_scenario=selected_scenario,
        risk_driver_breakdown=risk_driver_breakdown,
        top_news_events=top_news,
        hedge_simulation=hedge_simulation,
        trace_url=trace_url,
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


def set_stream_trace_url_for_run(run_id: str, trace_url: str) -> None:
    payload = _run_results.get(run_id)
    if payload is not None:
        payload.stream_trace_url = trace_url


def get_traceability_for_run(run_id: str) -> dict | None:
    payload = _run_results.get(run_id)
    context = _run_contexts.get(run_id)
    if payload is None or context is None:
        return None
    return {
        "run_id": run_id,
        "recommendation_trace_url": payload.trace_url,
        "stream_trace_url": payload.stream_trace_url,
        "langfuse_trace_available": bool(payload.trace_url),
        "stream_trace_available": bool(payload.stream_trace_url),
        "context_length": len(context),
        "context_preview": context[:4000],
        "context_includes": {
            "news_events": "news_events" in context,
            "weather": "port_weather_risk" in context,
            "resin": "resin_benchmark" in context or "resin_price_scenario" in context,
            "risk_driver_breakdown": "risk_driver_breakdown" in context,
            "monte_carlo": "landed_cost_monte_carlo" in context,
            "macro": "macro" in context,
        },
    }


def simulate_hedge_for_run(run_id: str, hedge_ratio: float) -> HedgeScenarioResult | None:
    run_payload = _run_results.get(run_id)
    mc_inputs = _run_monte_carlo_inputs.get(run_id)
    if run_payload is None or mc_inputs is None:
        return None

    winner_quote_id = str(mc_inputs["winner_quote_id"])
    quote_input = next(
        (item for item in mc_inputs["quote_inputs"] if str(item.quote.quote_id) == winner_quote_id),
        None,
    )
    if quote_input is None:
        return None

    mc_service = LandedCostMonteCarloService()
    scenario = mc_service.simulate_quote(
        run_id=run_id,
        quote_input=quote_input,
        quantity_mt=float(mc_inputs["quantity_mt"]),
        hedge_ratio=hedge_ratio,
        risk_driver_breakdown=mc_inputs["risk_driver_breakdown"],
        resin_price_scenario=mc_inputs["resin_price_scenario"],
    )
    unhedged_scenario = mc_service.simulate_quote(
        run_id=run_id,
        quote_input=quote_input,
        quantity_mt=float(mc_inputs["quantity_mt"]),
        hedge_ratio=0.0,
        risk_driver_breakdown=mc_inputs["risk_driver_breakdown"],
        resin_price_scenario=mc_inputs["resin_price_scenario"],
    )
    result = mc_service.to_hedge_result(scenario=scenario, unhedged_scenario=unhedged_scenario)

    run_payload.selected_scenario = scenario
    run_payload.hedge_simulation = result
    run_payload.landed_cost_scenarios[winner_quote_id] = scenario
    return result


def draft_bank_instruction_for_run(run_id: str, hedge_ratio: float) -> BankInstructionDraft | None:
    run_payload = _run_results.get(run_id)
    mc_inputs = _run_monte_carlo_inputs.get(run_id)
    if run_payload is None or mc_inputs is None or not run_payload.ranked_quotes:
        return None

    winner = run_payload.ranked_quotes[0]
    quote = winner.quote
    scenario = run_payload.hedge_simulation or simulate_hedge_for_run(run_id, hedge_ratio)
    requested_strike = _fx_spot_for_quote(mc_inputs["quote_inputs"], str(quote.quote_id))
    amount = (quote.unit_price or 0.0) * float(mc_inputs["quantity_mt"])
    risk_rationale = _build_hedge_rationale(run_payload, scenario)
    service = LandedCostMonteCarloService()
    fallback = service.fallback_bank_instruction(
        supplier_name=quote.supplier_name or "Selected supplier",
        target_currency=quote.currency or "USD",
        amount=amount,
        tenor_days=30,
        requested_strike_rate=requested_strike,
        hedge_ratio=hedge_ratio,
        risk_rationale=risk_rationale,
    )

    try:
        provider = build_llm_provider()
        raw_text = provider.reason_about_recommendation(
            {
                "task": "Return strict JSON for a Malaysian bank forward-contract instruction letter.",
                "required_schema": fallback.model_dump(mode="json"),
                "analysis": {
                    "run_id": run_id,
                    "supplier": quote.supplier_name,
                    "target_currency": quote.currency,
                    "amount": amount,
                    "tenor_days": 30,
                    "hedge_ratio": hedge_ratio,
                    "requested_strike_rate": requested_strike,
                    "risk_rationale": risk_rationale,
                    "fan_chart_direction": _fan_chart_direction(scenario),
                },
                "constraints": [
                    "Return JSON only.",
                    "Do not generate a PDF or binary content.",
                    "Write formal but concise bank instruction wording.",
                ],
            }
        )
        payload = _extract_json_object(raw_text)
        merged = fallback.model_dump(mode="json")
        merged.update({key: value for key, value in payload.items() if value not in (None, "")})
        merged["generated_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        return BankInstructionDraft(**merged)
    except Exception as exc:
        # No fallback — re-raise so the caller knows the LLM/Langfuse call failed.
        logger.error("Bank instruction LLM draft failed for run %s: %s", run_id, exc)
        raise


def _fx_spot_for_quote(quote_inputs: list[MonteCarloQuoteInput], quote_id: str) -> float:
    quote_input = next((item for item in quote_inputs if str(item.quote.quote_id) == quote_id), None)
    return float(quote_input.fx_sim.current_spot) if quote_input else 4.7


def _build_hedge_rationale(
    run_payload: AnalysisResultPayload,
    scenario: HedgeScenarioResult | None,
) -> str:
    direction = _fan_chart_direction(scenario)
    if direction == "down":
        timing_note = "The 30-day fan chart trends lower, so management may wait or requote if supply urgency permits."
    elif direction == "up":
        timing_note = "The 30-day fan chart trends higher, so hedging now reduces the risk of landed-cost escalation."
    else:
        timing_note = "The 30-day fan chart is broadly stable, so the hedge is sized to control tail risk rather than chase price direction."

    risk = run_payload.risk_driver_breakdown
    driver_note = ""
    if risk:
        values = risk.model_dump(exclude={"notes"})
        top_driver = max(values.items(), key=lambda item: float(item[1]))
        driver_note = f" The largest normalized risk driver is {top_driver[0].replace('_', ' ')} at {top_driver[1]:.2f}."
    return f"{timing_note}{driver_note}"


def _fan_chart_direction(scenario: HedgeScenarioResult | LandedCostScenario | None) -> str:
    if scenario is None or not scenario.p50_envelope:
        return "flat"
    start = scenario.p50_envelope[0]
    end = scenario.p50_envelope[-1]
    if end <= start * 0.985:
        return "down"
    if end >= start * 1.015:
        return "up"
    return "flat"


def _extract_json_object(raw_text: str) -> dict:
    content = raw_text.strip()
    if content.startswith("```"):
        chunks = [chunk for chunk in content.split("```") if "{" in chunk and "}" in chunk]
        content = chunks[0].replace("json", "", 1).strip() if chunks else content
    start = content.find("{")
    end = content.rfind("}")
    if start >= 0 and end > start:
        content = content[start : end + 1]
    return json.loads(content)
