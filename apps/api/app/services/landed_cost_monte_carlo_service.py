from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

import numpy as np

from app.repositories.snapshot_repository import SnapshotRepository
from app.schemas.analysis import (
    BankInstructionDraft,
    FxSimulationResult,
    HedgeScenarioResult,
    LandedCostResult,
    LandedCostScenario,
    RiskDriverBreakdown,
)
from app.schemas.quote import ExtractedQuote
from app.schemas.reference import FreightRate, SupplierSeed, TariffRule


@dataclass(frozen=True)
class MonteCarloQuoteInput:
    quote: ExtractedQuote
    cost_result: LandedCostResult
    fx_sim: FxSimulationResult
    freight: FreightRate
    tariff: TariffRule
    supplier: SupplierSeed


class LandedCostMonteCarloService:
    def __init__(
        self,
        *,
        snapshot_repository: SnapshotRepository | None = None,
        horizon_days: int = 30,
        n_paths: int = 2000,
    ) -> None:
        self.snapshot_repository = snapshot_repository or SnapshotRepository()
        self.horizon_days = horizon_days
        self.n_paths = n_paths

    def build_risk_driver_breakdown(
        self,
        *,
        macro_context: dict[str, Any] | None,
        top_news: list[dict[str, Any]] | None,
        port_risks: list[dict[str, Any]] | None,
        resin_price_scenario: dict[str, Any] | None,
        tariff_rate_pct: float,
    ) -> RiskDriverBreakdown:
        notes: dict[str, str] = {}
        news = top_news or []
        logistics_news = self._news_score(news, "logistics")
        finance_news = self._news_score(news, "finance")
        geopolitical_news = self._news_score(news, "geopolitical")
        tariff_news = self._keyword_score(news, ("tariff", "import", "policy", "duties"))
        if news:
            notes["news"] = self._news_note(news)

        macro_score = self._macro_score(macro_context or {}, notes)
        weather_score = self._weather_score(port_risks or [], notes)
        holiday_score = self._holiday_score(notes)
        oil_score = self._oil_score(notes)
        resin_score = self._resin_benchmark_signal(resin_price_scenario, notes)

        tariff_score = min(1.0, tariff_rate_pct / 20.0 + tariff_news * 0.35)
        notes["tariff"] = f"Reference tariff baseline is {tariff_rate_pct:.2f}%; tariff/news overlay score is {tariff_score:.2f}."
        freight_score = min(1.0, 0.30 * oil_score + 0.25 * weather_score + 0.25 * logistics_news + 0.15 * holiday_score + 0.05 * geopolitical_news)
        fx_score = min(1.0, 0.45 * macro_score + 0.30 * finance_news + 0.15 * geopolitical_news + 0.10 * oil_score)
        news_score = min(1.0, max(logistics_news, finance_news, geopolitical_news, tariff_news))

        return RiskDriverBreakdown(
            tariff_rate=round(tariff_score, 3),
            freight_rate=round(freight_score, 3),
            fx_currency=round(fx_score, 3),
            oil_price=round(oil_score, 3),
            weather_risk=round(weather_score, 3),
            holidays=round(holiday_score, 3),
            macro_economy=round(macro_score, 3),
            news_events=round(news_score, 3),
            pp_resin_benchmark=round(resin_score, 3),
            notes=notes,
        )

    def build_scenarios(
        self,
        *,
        run_id: str,
        quote_inputs: list[MonteCarloQuoteInput],
        quantity_mt: float,
        hedge_ratio: float,
        risk_driver_breakdown: RiskDriverBreakdown,
        resin_price_scenario: dict[str, Any] | None,
    ) -> dict[str, LandedCostScenario]:
        return {
            str(quote_input.quote.quote_id): self.simulate_quote(
                run_id=run_id,
                quote_input=quote_input,
                quantity_mt=quantity_mt,
                hedge_ratio=hedge_ratio,
                risk_driver_breakdown=risk_driver_breakdown,
                resin_price_scenario=resin_price_scenario,
            )
            for quote_input in quote_inputs
        }

    def simulate_quote(
        self,
        *,
        run_id: str,
        quote_input: MonteCarloQuoteInput,
        quantity_mt: float,
        hedge_ratio: float,
        risk_driver_breakdown: RiskDriverBreakdown,
        resin_price_scenario: dict[str, Any] | None,
    ) -> LandedCostScenario:
        quote = quote_input.quote
        if quote.unit_price is None:
            raise ValueError("Quote unit price is required for landed-cost Monte Carlo.")

        hedge = min(1.0, max(0.0, hedge_ratio / 100.0))
        days = np.arange(0, self.horizon_days + 1)
        rng = np.random.default_rng(self._stable_seed(run_id, str(quote.quote_id)))

        fx_spot = max(float(quote_input.fx_sim.current_spot), 0.000001)
        fx_vol = max(float(quote_input.fx_sim.implied_vol), 0.02)
        fx_vol *= 1.0 + (0.35 * risk_driver_breakdown.macro_economy) + (0.25 * risk_driver_breakdown.news_events)
        fx_drift = 0.00045 * risk_driver_breakdown.macro_economy
        fx_paths = self._geometric_paths(
            rng=rng,
            spot=fx_spot,
            daily_drift=fx_drift,
            daily_vol=fx_vol / math.sqrt(252),
            days=days,
        )
        effective_fx = hedge * fx_spot + (1.0 - hedge) * fx_paths

        material_paths = quote.unit_price * quantity_mt * effective_fx

        freight_base_myr = self._freight_base_myr(
            quote_input=quote_input,
            quantity_mt=quantity_mt,
            fx_spot=fx_spot,
        )
        freight_paths = self._freight_paths(
            rng=rng,
            days=days,
            base_myr=freight_base_myr,
            risk_driver_breakdown=risk_driver_breakdown,
        )

        tariff_rate = quote_input.tariff.tariff_rate_pct / 100.0
        tariff_paths = material_paths * tariff_rate
        tariff_paths += self._tariff_policy_shock(
            rng=rng,
            material_paths=material_paths,
            tariff_rate=tariff_rate,
            tariff_risk=risk_driver_breakdown.tariff_rate,
        )

        delay_paths = self._delay_cost_paths(
            rng=rng,
            days=days,
            quantity_mt=quantity_mt,
            risk_driver_breakdown=risk_driver_breakdown,
        )

        moq_penalty = quote_input.cost_result.moq_penalty
        trust_penalty = quote_input.cost_result.trust_penalty
        total = material_paths + freight_paths + tariff_paths + delay_paths + moq_penalty + trust_penalty

        p10 = np.percentile(total, 10, axis=0)
        p50 = np.percentile(total, 50, axis=0)
        p90 = np.percentile(total, 90, axis=0)
        widths = p90 - p10
        method = "deterministic_9_aspect_monte_carlo"
        if resin_price_scenario:
            method = "deterministic_monte_carlo_with_resin_benchmark_context_only"

        p90_spread = p90[-1] - p50[-1]
        margin_flag = bool(p90[-1] > quote_input.cost_result.total_landed_p50 * 1.12 or p90_spread > p50[-1] * 0.08)

        return LandedCostScenario(
            quote_id=str(quote.quote_id),
            currency=quote.currency or "MYR",
            horizon_days=self.horizon_days + 1,
            hedge_ratio=round(hedge_ratio, 2),
            current_landed_cost=round(float(quote_input.cost_result.total_landed_p50), 2),
            p10_envelope=[round(float(value), 2) for value in p10],
            p50_envelope=[round(float(value), 2) for value in p50],
            p90_envelope=[round(float(value), 2) for value in p90],
            risk_width_envelope=[round(float(value), 2) for value in widths],
            p90_margin_wipeout_flag=margin_flag,
            method=method,
            as_of=date.today().isoformat(),
        )

    def to_hedge_result(
        self,
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

    def fallback_bank_instruction(
        self,
        *,
        supplier_name: str,
        target_currency: str,
        amount: float,
        tenor_days: int,
        requested_strike_rate: float,
        hedge_ratio: float,
        risk_rationale: str,
    ) -> BankInstructionDraft:
        return BankInstructionDraft(
            title="LETTER OF INSTRUCTION: FORWARD EXCHANGE CONTRACT",
            sme_name="LintasNiaga SME Client",
            supplier_name=supplier_name,
            target_currency=target_currency,
            amount=round(amount, 2),
            tenor_days=tenor_days,
            requested_strike_rate=round(requested_strike_rate, 6),
            hedge_ratio=round(hedge_ratio, 2),
            business_justification=(
                "We request the bank to arrange a forward exchange contract for the stated procurement exposure. "
                f"The hedge is intended to reduce foreign-exchange volatility during the {tenor_days}-day purchase window while "
                "preserving visibility of non-FX logistics, resin, weather, and policy risks."
            ),
            risk_rationale=risk_rationale,
            generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        )

    @staticmethod
    def _stable_seed(run_id: str, quote_id: str) -> int:
        digest = hashlib.sha256(f"{run_id}:{quote_id}".encode("utf-8")).hexdigest()
        return int(digest[:16], 16) % (2**32)

    def _geometric_paths(
        self,
        *,
        rng: np.random.Generator,
        spot: float,
        daily_drift: float,
        daily_vol: float,
        days: np.ndarray,
    ) -> np.ndarray:
        shocks = rng.normal(loc=daily_drift, scale=daily_vol, size=(self.n_paths, len(days)))
        shocks[:, 0] = 0.0
        cumulative = np.cumsum(shocks, axis=1)
        return spot * np.exp(cumulative)

    @staticmethod
    def _freight_base_myr(*, quote_input: MonteCarloQuoteInput, quantity_mt: float, fx_spot: float) -> float:
        if quote_input.freight.rate_unit.lower() == "mt":
            freight_base = quote_input.freight.rate_value * quantity_mt
        else:
            freight_base = quote_input.freight.rate_value * (quantity_mt / 20.0)
        return freight_base * fx_spot

    def _freight_paths(
        self,
        *,
        rng: np.random.Generator,
        days: np.ndarray,
        base_myr: float,
        risk_driver_breakdown: RiskDriverBreakdown,
    ) -> np.ndarray:
        daily_drift = 0.0004 * risk_driver_breakdown.oil_price
        daily_vol = 0.004 + 0.012 * risk_driver_breakdown.freight_rate
        shocks = rng.normal(loc=daily_drift, scale=daily_vol, size=(self.n_paths, len(days)))
        shocks[:, 0] = 0.0
        freight_factor = np.clip(np.exp(np.cumsum(shocks, axis=1)), 0.85, 1.35)
        return base_myr * freight_factor

    def _tariff_policy_shock(
        self,
        *,
        rng: np.random.Generator,
        material_paths: np.ndarray,
        tariff_rate: float,
        tariff_risk: float,
    ) -> np.ndarray:
        if tariff_risk < 0.35:
            return np.zeros_like(material_paths)
        probability = min(0.04, 0.01 + tariff_risk * 0.03)
        event_by_path = rng.random((self.n_paths, 1)) < probability
        shock_rate = min(0.025, tariff_rate * 0.5 + 0.005)
        return np.where(event_by_path, material_paths * shock_rate, 0.0)

    def _delay_cost_paths(
        self,
        *,
        rng: np.random.Generator,
        days: np.ndarray,
        quantity_mt: float,
        risk_driver_breakdown: RiskDriverBreakdown,
    ) -> np.ndarray:
        probability = min(
            0.45,
            0.05
            + 0.15 * risk_driver_breakdown.weather_risk
            + 0.10 * risk_driver_breakdown.holidays
            + 0.10 * risk_driver_breakdown.news_events,
        )
        delay_days = rng.poisson(lam=max(0.2, probability * 4.0), size=(self.n_paths, 1))
        active = rng.random((self.n_paths, 1)) < probability
        delay_cost = np.where(active, delay_days * quantity_mt * 8.0, 0.0)
        ramp = np.clip(days / max(self.horizon_days, 1), 0.0, 1.0)
        return delay_cost * ramp

    @staticmethod
    def _macro_score(macro_context: dict[str, Any], notes: dict[str, str]) -> float:
        score = 0.0
        trade = macro_context.get("trade") or {}
        ipi = macro_context.get("ipi") or {}
        if trade.get("status") == "DANGER":
            score += 0.55
            notes["macro_trade"] = str(trade.get("message", "Trade deficit increases MYR weakening risk."))
        elif trade.get("message"):
            notes["macro_trade"] = str(trade["message"])
        if ipi.get("status") == "DANGER":
            score += 0.25
            notes["macro_ipi"] = str(ipi.get("message", "Manufacturing contraction increases inventory caution."))
        elif ipi.get("message"):
            notes["macro_ipi"] = str(ipi["message"])
        return min(1.0, score)

    @staticmethod
    def _news_score(news: list[dict[str, Any]], category: str) -> float:
        scores = [
            float(item.get("relevance_score", 0.0))
            for item in news
            if str(item.get("category", "")).lower() == category
        ]
        return min(1.0, max(scores, default=0.0))

    @staticmethod
    def _keyword_score(news: list[dict[str, Any]], keywords: tuple[str, ...]) -> float:
        score = 0.0
        for item in news:
            text = json.dumps(item, ensure_ascii=True).lower()
            if any(keyword in text for keyword in keywords):
                score = max(score, float(item.get("relevance_score", 0.4)))
        return min(1.0, score)

    @staticmethod
    def _weather_score(port_risks: list[dict[str, Any]], notes: dict[str, str]) -> float:
        if not port_risks:
            notes["weather"] = "No weather snapshot found; using neutral weather risk."
            return 0.0
        max_item = max(port_risks, key=lambda item: float(item.get("max_risk_score", 0.0)))
        max_score = float(max_item.get("max_risk_score", 0.0))
        port_name = max_item.get("port_name") or max_item.get("port_code") or "tracked port"
        horizon = max_item.get("forecast_horizon_days")
        endpoint = max_item.get("endpoint_used")
        high_risk_slots = max_item.get("high_risk_slots") or []
        slot_note = ""
        if high_risk_slots:
            first_slot = high_risk_slots[0]
            slot_note = (
                f"; top risk slot {first_slot.get('forecast_date')} has "
                f"{first_slot.get('raw_weather_summary')} with wind {first_slot.get('wind_speed_ms')} m/s "
                f"and precipitation {first_slot.get('precipitation_mm')} mm"
            )
        notes["weather"] = (
            f"OpenWeather shows highest port risk at {port_name}: {max_score:.0f}/100 "
            f"around {max_item.get('worst_slot_date', 'the forecast window')} "
            f"({max_item.get('raw_weather_summary', 'weather risk')}). "
            f"Forecast source {endpoint or 'openweather'} covers {horizon or 'available'} day(s)"
            f"{slot_note}."
        )
        return min(1.0, max_score / 100.0)

    def _holiday_score(self, notes: dict[str, str]) -> float:
        snapshot = self.snapshot_repository.read_latest("holidays")
        if snapshot is None or not snapshot.data:
            notes["holidays"] = "No holiday snapshot found; using neutral holiday risk."
            return 0.0
        start = date.today()
        end = start + timedelta(days=self.horizon_days)
        holidays_in_window: list[dict[str, Any]] = []
        for item in snapshot.data:
            try:
                holiday_date = date.fromisoformat(str(item.get("date")))
            except ValueError:
                continue
            if start <= holiday_date <= end and item.get("is_holiday", True):
                holidays_in_window.append(item)
        holiday_count = len(holidays_in_window)
        if holiday_count:
            examples = "; ".join(
                f"{item.get('country_name') or item.get('country_code')} {item.get('holiday_name')} on {item.get('date')}"
                for item in holidays_in_window[:6]
            )
            notes["holidays"] = (
                f"{holiday_count} public holiday/closure day(s) fall inside the next {self.horizon_days} days: "
                f"{examples}."
            )
        else:
            summary = next((item for item in snapshot.data if item.get("lead_time_risk") == "summary"), None)
            notes["holidays"] = str(
                (summary or {}).get(
                    "glm_context",
                    f"No Malaysia/China/Thailand/Indonesia public holidays fall inside the next {self.horizon_days} days.",
                )
            )
        return min(1.0, holiday_count / 6.0)

    def _oil_score(self, notes: dict[str, str]) -> float:
        snapshot = self.snapshot_repository.read_latest("energy/BZ=F") or self.snapshot_repository.read_latest("energy")
        if snapshot is None or len(snapshot.data) < 2:
            notes["oil"] = "No Brent energy snapshot found; using neutral oil risk."
            return 0.0
        records = sorted(snapshot.data, key=lambda item: str(item.get("date", "")))
        latest = float(records[-1].get("close", 0.0))
        lookback = float(records[max(0, len(records) - 8)].get("close", latest))
        if latest <= 0 or lookback <= 0:
            return 0.0
        move = (latest - lookback) / lookback
        notes["oil"] = f"Brent/energy snapshot moved from {lookback:.2f} to {latest:.2f} over the latest lookback, a {move:.1%} move."
        return min(1.0, max(0.0, move * 10.0 + 0.15))

    @staticmethod
    def _resin_benchmark_signal(resin_price_scenario: dict[str, Any] | None, notes: dict[str, str]) -> float:
        if not resin_price_scenario:
            notes["resin"] = "No PP resin snapshot found; using neutral resin risk."
            return 0.0
        current = float(resin_price_scenario.get("current_price") or 0.0)
        history_move = abs(float(resin_price_scenario.get("history_move_pct") or 0.0))
        observations = int(resin_price_scenario.get("history_observation_count") or 0)
        if current <= 0:
            return 0.0
        notes["resin"] = str(
            resin_price_scenario.get("glm_context")
            or f"SunSirs PP benchmark current price is {current:,.2f}; use this as quote-vs-market evidence only."
        )
        # This is a benchmark explanation signal only. It is not used to move
        # material-price paths in the Monte Carlo fan chart.
        scarcity_penalty = 0.2 if observations < 7 else 0.0
        return min(1.0, history_move / 10.0 + scarcity_penalty)

    @staticmethod
    def _news_note(news: list[dict[str, Any]]) -> str:
        top = sorted(news, key=lambda item: float(item.get("relevance_score", 0.0)), reverse=True)[:3]
        if not top:
            return "No high-relevance news event was selected."
        parts = []
        for item in top:
            title = str(item.get("title") or "Untitled news").strip()
            source = str(item.get("source") or "unknown source").strip()
            score = float(item.get("relevance_score", 0.0))
            parts.append(f"'{title}' from {source} (score {score:.2f})")
        return "Top GNews signals: " + "; ".join(parts) + "."
