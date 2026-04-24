from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field

from app.schemas.quote import ExtractedQuote


class FxSimulationResult(BaseModel):
    pair: str
    current_spot: float
    implied_vol: float
    p10_envelope: List[float]
    p50_envelope: List[float]
    p90_envelope: List[float]
    horizon_days: int


class LandedCostResult(BaseModel):
    quote_id: str
    material_cost_myr_p10: float
    material_cost_myr_p50: float
    material_cost_myr_p90: float
    freight_cost_myr: float
    tariff_cost_myr: float
    moq_penalty: float
    trust_penalty: float
    total_landed_p10: float
    total_landed_p50: float
    total_landed_p90: float


class MarketPriceRisk(BaseModel):
    quote_id: str
    quote_price_value: float
    quote_currency: str
    quote_price_myr_per_mt: float
    benchmark_price_value: float
    benchmark_currency: str
    benchmark_price_myr_per_mt: float
    premium_pct: float
    risk_label: Literal["below_market", "fair", "premium", "high_premium"]
    source_url: str
    as_of: str


class ResinPriceScenario(BaseModel):
    series_key: str
    source: str
    currency: str
    unit: str
    current_price: float
    as_of: str
    method: str
    horizon_days: int
    p10_envelope: List[float]
    p50_envelope: List[float]
    p90_envelope: List[float]


class RiskDriverBreakdown(BaseModel):
    tariff_rate: float = 0.0
    freight_rate: float = 0.0
    fx_currency: float = 0.0
    oil_price: float = 0.0
    weather_risk: float = 0.0
    holidays: float = 0.0
    macro_economy: float = 0.0
    news_events: float = 0.0
    pp_resin_benchmark: float = 0.0
    notes: Dict[str, str] = Field(default_factory=dict)


class LandedCostScenario(BaseModel):
    quote_id: str
    currency: str
    horizon_days: int
    hedge_ratio: float
    current_landed_cost: float
    p10_envelope: List[float]
    p50_envelope: List[float]
    p90_envelope: List[float]
    risk_width_envelope: List[float]
    p90_margin_wipeout_flag: bool
    method: str
    as_of: str


class RankedQuote(BaseModel):
    rank: int
    delta_vs_winner: float
    cost_result: LandedCostResult


class RankedQuoteDetail(BaseModel):
    rank: int
    delta_vs_winner: float
    quote: ExtractedQuote
    cost_result: LandedCostResult
    reliability_score: float | None = None
    market_price_risk: MarketPriceRisk | None = None


class BackupOption(BaseModel):
    quote_id: str
    reason: str
    premium_vs_winner: float


class RecommendationCard(BaseModel):
    recommended_quote_id: str
    expected_landed_cost_myr: float
    confidence_score: float
    backup_options: List[BackupOption]
    mode: Literal["comparison", "single_quote"] = "comparison"
    evaluation_label: Literal["proceed", "review_carefully", "do_not_recommend"] | None = None
    timing: str
    hedge_pct: float
    reasons: List[str]
    caveat: str | None = None
    why_not_others: dict[str, str]
    impact_summary: str | None = None


class HedgeScenarioResult(BaseModel):
    hedge_ratio: float
    adjusted_p50: float
    adjusted_p90: float
    impact_vs_unhedged: float
    quote_id: str | None = None
    horizon_days: int = 30
    p10_envelope: List[float] = Field(default_factory=list)
    p50_envelope: List[float] = Field(default_factory=list)
    p90_envelope: List[float] = Field(default_factory=list)
    risk_width_envelope: List[float] = Field(default_factory=list)
    p90_margin_wipeout_flag: bool = False
    method: str = "legacy_adjustment"


class BankInstructionDraft(BaseModel):
    title: str
    sme_name: str
    supplier_name: str
    target_currency: str
    amount: float
    tenor_days: int
    requested_strike_rate: float
    hedge_ratio: float
    business_justification: str
    risk_rationale: str
    generated_at: str


class AnalysisResultPayload(BaseModel):
    run_id: str
    recommendation: RecommendationCard
    ranked_quotes: List[RankedQuoteDetail]
    fx_simulations: Dict[str, FxSimulationResult]
    resin_benchmark: Dict[str, Any] | None = None
    market_price_risks: List[MarketPriceRisk] = Field(default_factory=list)
    resin_price_scenario: ResinPriceScenario | None = None
    landed_cost_scenarios: Dict[str, LandedCostScenario] = Field(default_factory=dict)
    selected_scenario: LandedCostScenario | None = None
    risk_driver_breakdown: RiskDriverBreakdown | None = None
    hedge_simulation: HedgeScenarioResult | None = None
    trace_url: str | None = None


class FxLatestPoint(BaseModel):
    pair: str
    close: float
    as_of: str | None = None
