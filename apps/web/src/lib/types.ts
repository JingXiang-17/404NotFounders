export interface QuoteUpload {
  files: File[];
  requiredQuantity: number;
  urgency: "Normal" | "Urgent";
}

export interface ExtractedQuote {
  supplier_name: string;
  price: number;
  currency: string;
  incoterm: string;
  quantity: number;
  date: string;
}

export interface QuoteValidationResult {
  is_valid: boolean;
  errors: string[];
  repaired_quote?: ExtractedQuote;
}

export interface SnapshotEnvelope<T> {
  dataset: string;
  source: string;
  fetched_at: string;
  as_of: string;
  status: string;
  record_count: number;
  data: T[];
}
