export interface QuoteUpload {
  upload_id: string;
  filename: string;
  storage_path: string;
  uploaded_at: string;
  status: "pending" | "extracted" | "validated" | "invalid";
}

export interface ExtractedQuote {
  quote_id: string;
  upload_id: string;
  supplier_name: string | null;
  origin_port_or_country: string | null;
  incoterm: string | null;
  unit_price: number | null;
  currency: string | null;
  moq: number | null;
  lead_time_days: number | null;
  payment_terms: string | null;
  extraction_confidence: number | null;
}

export interface QuoteValidationResult {
  quote_id: string;
  status: "valid" | "invalid_fixable" | "invalid_out_of_scope";
  reason_codes: string[];
  missing_fields: string[];
}

export interface QuoteState {
  upload: QuoteUpload;
  extracted_quote: ExtractedQuote | null;
  validation: QuoteValidationResult | null;
}

export interface SnapshotEnvelope<T> {
  dataset: string;
  source: string;
  fetched_at: string;
  as_of: string | null;
  status: string;
  record_count: number;
  data: T[];
}

export interface FxLatestPoint {
  pair: string;
  close: number;
  as_of: string | null;
}

export interface FxSimulationResult {
  pair: string;
  current_spot: number;
  implied_vol: number;
  p10_envelope: number[];
  p50_envelope: number[];
  p90_envelope: number[];
  horizon_days: number;
}

export interface LandedCostResult {
  quote_id: string;
  material_cost_myr_p10: number;
  material_cost_myr_p50: number;
  material_cost_myr_p90: number;
  freight_cost_myr: number;
  tariff_cost_myr: number;
  moq_penalty: number;
  trust_penalty: number;
  total_landed_p10: number;
  total_landed_p50: number;
  total_landed_p90: number;
}

export interface MarketPriceRisk {
  quote_id: string;
  quote_price_value: number;
  quote_currency: string;
  quote_price_myr_per_mt: number;
  benchmark_price_value: number;
  benchmark_currency: string;
  benchmark_price_myr_per_mt: number;
  premium_pct: number;
  risk_label: "below_market" | "fair" | "premium" | "high_premium";
  source_url: string;
  as_of: string;
}

export interface ResinPriceScenario {
  series_key: string;
  source: string;
  currency: string;
  unit: string;
  current_price: number;
  as_of: string;
  method: string;
  p10_envelope: number[];
  p50_envelope: number[];
  p90_envelope: number[];
  horizon_days: number;
}

export interface RiskDriverBreakdown {
  tariff_rate: number;
  freight_rate: number;
  fx_currency: number;
  oil_price: number;
  weather_risk: number;
  holidays: number;
  macro_economy: number;
  news_events: number;
  pp_resin_benchmark: number;
  notes: Record<string, string>;
}

export interface LandedCostScenario {
  quote_id: string;
  currency: string;
  horizon_days: number;
  hedge_ratio: number;
  current_landed_cost: number;
  p10_envelope: number[];
  p50_envelope: number[];
  p90_envelope: number[];
  risk_width_envelope: number[];
  p90_margin_wipeout_flag: boolean;
  method: string;
  as_of: string;
}

export interface RankedQuote {
  rank: number;
  delta_vs_winner: number;
  quote: ExtractedQuote;
  cost_result: LandedCostResult;
  reliability_score: number | null;
  market_price_risk: MarketPriceRisk | null;
}

export interface BackupOption {
  quote_id: string;
  reason: string;
  premium_vs_winner: number;
}

export interface RecommendationCard {
  recommended_quote_id: string;
  expected_landed_cost_myr: number;
  confidence_score: number;
  backup_options: BackupOption[];
  mode: "comparison" | "single_quote";
  evaluation_label: "proceed" | "review_carefully" | "do_not_recommend" | null;
  timing: "lock_now" | "wait" | string;
  hedge_pct: number;
  reasons: string[];
  caveat?: string | null;
  why_not_others: Record<string, string>;
  impact_summary: string | null;
}

export interface HedgeScenarioResult {
  hedge_ratio: number;
  adjusted_p50: number;
  adjusted_p90: number;
  impact_vs_unhedged: number;
  quote_id: string | null;
  horizon_days: number;
  p10_envelope: number[];
  p50_envelope: number[];
  p90_envelope: number[];
  risk_width_envelope: number[];
  p90_margin_wipeout_flag: boolean;
  method: string;
}

export interface BankInstructionDraft {
  title: string;
  sme_name: string;
  supplier_name: string;
  target_currency: string;
  amount: number;
  tenor_days: number;
  requested_strike_rate: number;
  hedge_ratio: number;
  business_justification: string;
  risk_rationale: string;
  generated_at: string;
}

export interface AnalysisRunResponse {
  run_id: string;
  recommendation: RecommendationCard;
}

export interface AnalysisResultPayload {
  run_id: string;
  recommendation: RecommendationCard;
  ranked_quotes: RankedQuote[];
  fx_simulations: Record<string, FxSimulationResult>;
  resin_benchmark: Record<string, unknown> | null;
  market_price_risks: MarketPriceRisk[];
  resin_price_scenario: ResinPriceScenario | null;
  landed_cost_scenarios: Record<string, LandedCostScenario>;
  selected_scenario: LandedCostScenario | null;
  risk_driver_breakdown: RiskDriverBreakdown | null;
  hedge_simulation: HedgeScenarioResult | null;
  trace_url: string | null;
}
