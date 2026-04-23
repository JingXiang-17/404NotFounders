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

export interface RankedQuote {
  rank: number;
  delta_vs_winner: number;
  quote: ExtractedQuote;
  cost_result: LandedCostResult;
  reliability_score: number | null;
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
  trace_url: string | null;
}
