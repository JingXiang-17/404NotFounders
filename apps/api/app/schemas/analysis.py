from __future__ import annotations

from typing import Dict, List, Literal

from pydantic import BaseModel

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


class AnalysisResultPayload(BaseModel):
    run_id: str
    recommendation: RecommendationCard
    ranked_quotes: List[RankedQuoteDetail]
    fx_simulations: Dict[str, FxSimulationResult]
    trace_url: str | None = None


class FxLatestPoint(BaseModel):
    pair: str
    close: float
    as_of: str | None = None
