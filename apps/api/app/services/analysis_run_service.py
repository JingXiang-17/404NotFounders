import logging
import json
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Dict, List, Tuple
from uuid import UUID

from app.core.constants import SUPPORTED_HS_CODE, SUPPORTED_IMPORT_COUNTRY
from app.core.exceptions import NoValidQuotes
from app.repositories.snapshot_repository import SnapshotRepository
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
from app.services.fx_service import simulate_fx_paths
from app.services.fx_simulation_service import LandedCostSimulationResult, simulate_landed_cost
from app.services.landed_cost_monte_carlo_service import (
    LandedCostMonteCarloService,
    MonteCarloQuoteInput,
)
from app.providers.llm_provider import build_llm_provider
from app.services.quote_ingest_service import get_quote_state
from app.services.recommendation_assembler_service import assemble_recommendation
from app.services.recommendation_engine_service import rank_quotes
from app.services.reference_data_service import load_all_reference_data
from app.services.holiday_service import ensure_holiday_snapshot_fresh
from app.services.macro_data_service import build_default_macro_service
from app.services.market_data_service import ensure_energy_snapshot_fresh, ensure_fx_snapshot_fresh
from app.services.news_event_service import build_default_news_service
from app.services.resin_benchmark_service import build_default_resin_service, ensure_resin_snapshot_fresh
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


def _require_success_snapshot(dataset: str, *, expected_source: str, min_records: int = 1) -> None:
    envelope = SnapshotRepository().read_latest(dataset)
    if envelope is None:
        raise ValueError(f"Strict analysis blocked: missing snapshot {dataset}.")
    if envelope.status != "success":
        raise ValueError(
            f"Strict analysis blocked: snapshot {dataset} status is {envelope.status}, expected success."
        )
    if envelope.source != expected_source:
        raise ValueError(
            f"Strict analysis blocked: snapshot {dataset} source is {envelope.source}, expected {expected_source}."
        )
    if envelope.record_count < min_records:
        raise ValueError(
            f"Strict analysis blocked: snapshot {dataset} has {envelope.record_count} rows, expected at least {min_records}."
        )


async def _refresh_and_validate_live_context(currencies: set[str]) -> None:
    for currency in currencies:
        await ensure_fx_snapshot_fresh(f"{currency}MYR", max_age_days=10, min_records=30)
    await ensure_energy_snapshot_fresh("BZ=F", max_age_days=10, min_records=30)

    macro_svc = build_default_macro_service()
    news_svc = build_default_news_service()
    weather_svc = build_default_weather_service()

    ipi = await macro_svc.refresh_ipi_snapshot()
    trade = await macro_svc.refresh_trade_snapshot()
    news = await news_svc.ensure_news_snapshot_fresh(max_age_minutes=60)
    resin = ensure_resin_snapshot_fresh(max_age_hours=24)
    weather = await weather_svc.refresh_weather_snapshot()
    holidays = ensure_holiday_snapshot_fresh(max_age_hours=24)

    for envelope, label in (
        (ipi, "macro"),
        (trade, "macro_trade"),
        (news, "news"),
        (resin, "resin"),
        (weather, "weather"),
        (holidays, "holidays"),
    ):
        if envelope.status != "success" or envelope.record_count < 1:
            raise ValueError(
                f"Strict analysis blocked: live refresh for {label} returned "
                f"status={envelope.status}, rows={envelope.record_count}."
            )

    for currency in currencies:
        _require_success_snapshot(f"fx/{currency}MYR", expected_source="yfinance", min_records=30)
    _require_success_snapshot("energy/BZ=F", expected_source="yfinance", min_records=30)
    _require_success_snapshot("macro", expected_source="opendosm:ipi")
    _require_success_snapshot("macro_trade", expected_source="opendosm:trade_sitc_1d")
    _require_success_snapshot("news", expected_source="gnews")
    _require_success_snapshot("resin", expected_source="SunSirs")
    _require_success_snapshot("weather", expected_source="openweathermap")
    _require_success_snapshot("holidays", expected_source="python-holidays")


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
    await _refresh_and_validate_live_context(currencies)

    fx_sims: Dict[str, FxSimulationResult] = {}
    for curr in currencies:
        pair = f"{curr}MYR"
        try:
            fx_sims[pair] = simulate_fx_paths(pair=pair)
        except Exception as exc:
            raise ValueError(
                f"Strict analysis blocked: FX simulation for {pair} failed after live yfinance refresh: {exc}"
            ) from exc

    weather_svc = build_default_weather_service()
    port_risks = weather_svc.get_port_risk_for_context()
    weather_delay_days = _weather_delay_days(port_risks)
    holidays_snapshot = SnapshotRepository().read_latest("holidays")

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
            simulation = await simulate_landed_cost(
                quote=quote,
                quantity_mt=quantity_mt,
                weather_delay_days=weather_delay_days,
                holiday_buffer_days=_holiday_buffer_days_for_quote(quote, holidays_snapshot),
                reference_data=reference_data,
                run_id=run_id,
                hedge_ratio_pct=0.0,
            )
            cost_result = _simulation_to_cost_result(simulation)
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

    macro_context = macro_svc.get_macro_context_for_ai()
    top_news = news_svc.get_top_events_for_context(top_n=5)
    resin_benchmark = resin_svc.get_latest_benchmark_for_context()
    market_price_risks = resin_svc.build_market_price_risks(list(quote_lookup.values()), fx_sims)
    resin_price_scenario = resin_svc.build_price_scenario()
    holiday_context = []
    if holidays_snapshot and holidays_snapshot.data:
        holiday_context = [
            item
            for item in holidays_snapshot.data
            if item.get("lead_time_risk") == "summary" or item.get("within_procurement_window")
        ][:20]
    risk_by_quote_id = {risk["quote_id"]: risk for risk in market_price_risks}
    mc_service = LandedCostMonteCarloService()
    risk_driver_breakdown = mc_service.build_risk_driver_breakdown(
        macro_context=macro_context,
        top_news=top_news,
        port_risks=port_risks,
        resin_price_scenario=resin_price_scenario,
        tariff_rate_pct=tariff_rule.tariff_rate_pct,
    )
    ai_context_scenarios = await _build_fx_oil_scenarios(
        run_id=run_id,
        quote_inputs=monte_carlo_inputs,
        quantity_mt=quantity_mt,
        hedge_ratio=0.0,
        reference_data=reference_data,
        weather_delay_days=weather_delay_days,
        holidays_snapshot=holidays_snapshot,
    )
    ai_context_winner_id = str(ranked_quotes[0].cost_result.quote_id)
    ai_context_selected_scenario = ai_context_scenarios.get(ai_context_winner_id)

    # Merge everything into macro_snapshot dict for context builder
    combined_snapshot: dict = {}
    combined_snapshot["tariff_reference"] = {
        "hs_code": tariff_rule.hs_code,
        "product_name": tariff_rule.product_name,
        "import_country": tariff_rule.import_country,
        "tariff_rate_pct": tariff_rule.tariff_rate_pct,
        "tariff_type": tariff_rule.tariff_type,
        "source_note": tariff_rule.source_note,
        "glm_context": (
            f"Tariff reference for HS {tariff_rule.hs_code} ({tariff_rule.product_name}) into "
            f"{tariff_rule.import_country}: {tariff_rule.tariff_rate_pct:.2f}% {tariff_rule.tariff_type}. "
            f"Source note: {tariff_rule.source_note}"
        ),
    }
    combined_snapshot["freight_reference_by_quote"] = [
        {
            "quote_id": str(item.quote.quote_id),
            "supplier_name": item.quote.supplier_name,
            "origin_country": item.freight.origin_country,
            "origin_port": item.freight.origin_port,
            "destination_port": item.freight.destination_port,
            "incoterm": item.freight.incoterm,
            "currency": item.freight.currency,
            "rate_value": item.freight.rate_value,
            "rate_unit": item.freight.rate_unit,
            "valid_from": item.freight.valid_from.isoformat(),
            "valid_to": item.freight.valid_to.isoformat(),
            "source_note": item.freight.source_note,
            "glm_context": (
                f"Freight reference for quote {item.quote.quote_id}: {item.freight.origin_port} to "
                f"{item.freight.destination_port}, {item.freight.rate_value:,.2f} "
                f"{item.freight.currency}/{item.freight.rate_unit}, valid {item.freight.valid_from.isoformat()} "
                f"to {item.freight.valid_to.isoformat()}. Source note: {item.freight.source_note}"
            ),
        }
        for item in monte_carlo_inputs
    ]
    oil_snapshot = SnapshotRepository().read_latest("energy/BZ=F")
    if oil_snapshot and oil_snapshot.data:
        records = sorted(oil_snapshot.data, key=lambda row: str(row.get("date", "")))
        latest_oil = records[-1]
        lookback_oil = records[max(0, len(records) - 8)]
        latest_close = float(latest_oil.get("close", 0.0) or 0.0)
        lookback_close = float(lookback_oil.get("close", latest_close) or latest_close)
        move_pct = ((latest_close - lookback_close) / lookback_close * 100.0) if lookback_close else 0.0
        combined_snapshot["oil_energy_snapshot"] = {
            "source": oil_snapshot.source,
            "series": "BZ=F Brent crude futures",
            "as_of": oil_snapshot.as_of,
            "record_count": oil_snapshot.record_count,
            "latest_date": latest_oil.get("date"),
            "latest_close": latest_close,
            "lookback_date": lookback_oil.get("date"),
            "lookback_close": lookback_close,
            "lookback_move_pct": round(move_pct, 2),
            "glm_context": (
                f"Brent crude yfinance snapshot BZ=F latest close {latest_close:.2f} on "
                f"{latest_oil.get('date')}; lookback close {lookback_close:.2f} on "
                f"{lookback_oil.get('date')} ({move_pct:.2f}% move). Oil affects freight surcharge pressure, "
                "not supplier resin benchmark sanity checks."
            ),
        }
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
        combined_snapshot["resin_usage_policy"] = (
            "PP resin benchmark is quote-vs-market evidence only. It must not be treated as a Monte Carlo "
            "material-price driver. Use it to explain below-market, fair, premium, high-premium, suspiciously low, "
            "or suspiciously high supplier quote risk."
        )
    if port_risks:
        combined_snapshot["port_weather_risk"] = port_risks
    if holiday_context:
        combined_snapshot["holiday_calendar"] = holiday_context
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

    if not ai_json:
        raise ValueError("Strict analysis blocked: GLM returned empty recommendation JSON.")
    if not trace_url:
        raise ValueError("Strict analysis blocked: Langfuse trace URL was not captured for GLM recommendation.")

    recommendation = assemble_recommendation(
        ranked_quotes=ranked_quotes,
        ai_json=ai_json,
        single_quote_mode=single_quote_mode,
    )
    scenario_by_quote = await _build_fx_oil_scenarios(
        run_id=run_id,
        quote_inputs=monte_carlo_inputs,
        quantity_mt=quantity_mt,
        hedge_ratio=recommendation.hedge_pct,
        reference_data=reference_data,
        weather_delay_days=weather_delay_days,
        holidays_snapshot=holidays_snapshot,
    )
    unhedged_scenario_by_quote = await _build_fx_oil_scenarios(
        run_id=run_id,
        quote_inputs=monte_carlo_inputs,
        quantity_mt=quantity_mt,
        hedge_ratio=0.0,
        reference_data=reference_data,
        weather_delay_days=weather_delay_days,
        holidays_snapshot=holidays_snapshot,
    )
    winner_quote_id = str(ranked_quotes[0].cost_result.quote_id)
    selected_scenario = scenario_by_quote.get(winner_quote_id)
    hedge_simulation = (
        _scenario_to_hedge_result(
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
        "reference_data": reference_data,
        "weather_delay_days": weather_delay_days,
        "holidays_snapshot": holidays_snapshot,
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
            "holidays": "holiday_calendar" in context,
            "resin": "resin_benchmark" in context or "resin_price_scenario" in context,
            "tariff": "tariff_reference" in context,
            "freight": "freight_reference_by_quote" in context,
            "oil": "oil_energy_snapshot" in context,
            "fx": "FX Simulation Summary" in context,
            "risk_driver_breakdown": "risk_driver_breakdown" in context,
            "monte_carlo": "landed_cost_monte_carlo" in context,
            "macro": "macro" in context,
        },
    }


async def _build_fx_oil_scenarios(
    *,
    run_id: str,
    quote_inputs: list[MonteCarloQuoteInput],
    quantity_mt: float,
    hedge_ratio: float,
    reference_data: dict,
    weather_delay_days: int,
    holidays_snapshot,
) -> dict[str, LandedCostScenario]:
    scenarios: dict[str, LandedCostScenario] = {}
    for quote_input in quote_inputs:
        simulation = await simulate_landed_cost(
            quote=quote_input.quote,
            quantity_mt=quantity_mt,
            weather_delay_days=weather_delay_days,
            holiday_buffer_days=_holiday_buffer_days_for_quote(quote_input.quote, holidays_snapshot),
            reference_data=reference_data,
            run_id=run_id,
            hedge_ratio_pct=hedge_ratio,
        )
        scenarios[str(quote_input.quote.quote_id)] = _simulation_to_scenario(
            simulation=simulation,
            hedge_ratio=hedge_ratio,
        )
    return scenarios


def _simulation_to_cost_result(simulation: LandedCostSimulationResult) -> LandedCostResult:
    return LandedCostResult(
        quote_id=simulation.quote_id,
        material_cost_myr_p10=simulation.material_p10,
        material_cost_myr_p50=simulation.material_p50,
        material_cost_myr_p90=simulation.material_p90,
        freight_cost_myr=simulation.freight_p50,
        tariff_cost_myr=simulation.tariff_p50,
        moq_penalty=simulation.moq_penalty,
        trust_penalty=simulation.trust_penalty,
        total_landed_p10=simulation.p10_at_delivery,
        total_landed_p50=simulation.p50_at_delivery,
        total_landed_p90=simulation.p90_at_delivery,
    )


def _simulation_to_scenario(
    *,
    simulation: LandedCostSimulationResult,
    hedge_ratio: float,
) -> LandedCostScenario:
    p10 = [band.p10 for band in simulation.daily_bands]
    p50 = [band.p50 for band in simulation.daily_bands]
    p90 = [band.p90 for band in simulation.daily_bands]
    widths = [round(high - low, 2) for low, high in zip(p10, p90, strict=False)]
    p90_spread = p90[-1] - p50[-1]
    margin_flag = bool(p90[-1] > p50[0] * 1.12 or p90_spread > p50[-1] * 0.08)
    return LandedCostScenario(
        quote_id=simulation.quote_id,
        currency=simulation.currency,
        horizon_days=simulation.horizon_days,
        hedge_ratio=round(hedge_ratio, 2),
        current_landed_cost=p50[0],
        p10_envelope=p10,
        p50_envelope=p50,
        p90_envelope=p90,
        risk_width_envelope=widths,
        p90_margin_wipeout_flag=margin_flag,
        method="snapshot_fx_oil_correlated_monte_carlo",
        as_of=date.today().isoformat(),
    )


def _scenario_to_hedge_result(
    *,
    scenario: LandedCostScenario,
    unhedged_scenario: LandedCostScenario | None,
) -> HedgeScenarioResult:
    adjusted_p50 = scenario.p50_envelope[-1]
    adjusted_p90 = scenario.p90_envelope[-1]
    unhedged_p90 = unhedged_scenario.p90_envelope[-1] if unhedged_scenario else adjusted_p90
    return HedgeScenarioResult(
        hedge_ratio=scenario.hedge_ratio,
        adjusted_p50=adjusted_p50,
        adjusted_p90=adjusted_p90,
        impact_vs_unhedged=round(unhedged_p90 - adjusted_p90, 2),
        quote_id=scenario.quote_id,
        horizon_days=scenario.horizon_days,
        p10_envelope=scenario.p10_envelope,
        p50_envelope=scenario.p50_envelope,
        p90_envelope=scenario.p90_envelope,
        risk_width_envelope=scenario.risk_width_envelope,
        p90_margin_wipeout_flag=scenario.p90_margin_wipeout_flag,
        method=scenario.method,
    )


def _weather_delay_days(port_risks: list[dict]) -> int:
    if not port_risks:
        return 0
    max_score = max(float(item.get("max_risk_score", 0.0) or 0.0) for item in port_risks)
    if max_score >= 85:
        return 7
    if max_score >= 70:
        return 5
    if max_score >= 50:
        return 3
    return 0


def _holiday_buffer_days_for_quote(quote: ExtractedQuote, holidays_snapshot) -> int:
    if holidays_snapshot is None or not holidays_snapshot.data:
        return 0
    origin_country = _infer_origin_country(quote.origin_port_or_country)
    relevant_countries = {"MY"}
    if origin_country:
        relevant_countries.add(origin_country)
    start = date.today()
    end = start + timedelta(days=max(1, int(quote.lead_time_days or 30)))
    holiday_days = 0
    for item in holidays_snapshot.data:
        if not item.get("is_holiday"):
            continue
        if item.get("country_code") not in relevant_countries:
            continue
        try:
            holiday_date = date.fromisoformat(str(item.get("date")))
        except ValueError:
            continue
        if start <= holiday_date <= end:
            holiday_days += 1
            if item.get("is_long_weekend"):
                holiday_days += 1
    return min(14, holiday_days)


async def simulate_hedge_for_run(run_id: str, hedge_ratio: float) -> HedgeScenarioResult | None:
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

    scenario_map = await _build_fx_oil_scenarios(
        run_id=run_id,
        quote_inputs=[quote_input],
        quantity_mt=float(mc_inputs["quantity_mt"]),
        hedge_ratio=hedge_ratio,
        reference_data=mc_inputs["reference_data"],
        weather_delay_days=int(mc_inputs["weather_delay_days"]),
        holidays_snapshot=mc_inputs["holidays_snapshot"],
    )
    unhedged_map = await _build_fx_oil_scenarios(
        run_id=run_id,
        quote_inputs=[quote_input],
        quantity_mt=float(mc_inputs["quantity_mt"]),
        hedge_ratio=0.0,
        reference_data=mc_inputs["reference_data"],
        weather_delay_days=int(mc_inputs["weather_delay_days"]),
        holidays_snapshot=mc_inputs["holidays_snapshot"],
    )
    scenario = scenario_map.get(winner_quote_id)
    if scenario is None:
        return None
    result = _scenario_to_hedge_result(
        scenario=scenario,
        unhedged_scenario=unhedged_map.get(winner_quote_id),
    )

    run_payload.selected_scenario = scenario
    run_payload.hedge_simulation = result
    run_payload.landed_cost_scenarios[winner_quote_id] = scenario
    return result


async def draft_bank_instruction_for_run(run_id: str, hedge_ratio: float) -> BankInstructionDraft | None:
    run_payload = _run_results.get(run_id)
    mc_inputs = _run_monte_carlo_inputs.get(run_id)
    if run_payload is None or mc_inputs is None or not run_payload.ranked_quotes:
        return None

    winner = run_payload.ranked_quotes[0]
    quote = winner.quote
    scenario = await simulate_hedge_for_run(run_id, hedge_ratio) or run_payload.hedge_simulation
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
    horizon_days = max(0, (scenario.horizon_days if scenario else 0) - 1)
    horizon_label = f"{horizon_days}-day" if horizon_days > 0 else "forecast"
    if direction == "down":
        timing_note = f"The {horizon_label} fan chart trends lower, so management may wait or requote if supply urgency permits."
    elif direction == "up":
        timing_note = f"The {horizon_label} fan chart trends higher, so hedging now reduces the risk of landed-cost escalation."
    else:
        timing_note = f"The {horizon_label} fan chart is broadly stable, so the hedge is sized to control tail risk rather than chase price direction."

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
