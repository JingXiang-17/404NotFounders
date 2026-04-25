"use client";

import { Suspense, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";

import { AnalysisShell } from "@/components/analysis-shell";
import { fetchApi } from "@/lib/api";
import { AnalysisRunResponse, ExtractedQuote, FxLatestPoint, QuoteState } from "@/lib/types";

const FLAG_BY_COUNTRY: Record<string, string> = {
  CN: "CN",
  TH: "TH",
  ID: "ID",
};

function inferCountryCode(value: string | null | undefined): string {
  const normalized = (value ?? "").toLowerCase();
  if (normalized.includes("china") || normalized.includes("ningbo") || normalized.includes("shenzhen")) {
    return "CN";
  }
  if (normalized.includes("thailand") || normalized.includes("bangkok")) {
    return "TH";
  }
  if (normalized.includes("indonesia") || normalized.includes("jakarta")) {
    return "ID";
  }
  return "";
}

function editableQuoteFromState(state: QuoteState): ExtractedQuote | null {
  return state.extracted_quote ? { ...state.extracted_quote } : null;
}

function ReviewPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const quoteIds = useMemo(
    () =>
      (searchParams.get("quoteIds") ?? "")
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean),
    [searchParams],
  );
  const quantityMt = Number(searchParams.get("quantity") ?? "0");
  const urgency = searchParams.get("urgency") ?? "normal";

  const [quoteOverrides, setQuoteOverrides] = useState<Record<string, ExtractedQuote>>({});
  const [hedgePreference, setHedgePreference] = useState("balance");

  const quotesQuery = useQuery({
    queryKey: ["review-quotes", quoteIds],
    enabled: quoteIds.length > 0,
    queryFn: async () => {
      const states = await Promise.all(quoteIds.map((quoteId) => fetchApi<QuoteState>(`/quotes/${quoteId}`)));
      return states;
    },
  });

  const extractedQuotesById = useMemo(() => {
    const nextLocalState: Record<string, ExtractedQuote> = {};
    quotesQuery.data?.forEach((state) => {
      if (state.extracted_quote) {
        nextLocalState[state.extracted_quote.quote_id] = editableQuoteFromState(state)!;
      }
    });
    return nextLocalState;
  }, [quotesQuery.data]);

  const localQuotes = useMemo(
    () => ({ ...extractedQuotesById, ...quoteOverrides }),
    [extractedQuotesById, quoteOverrides],
  );

  const fxQuery = useQuery({
    queryKey: ["fx-latest"],
    queryFn: () => fetchApi<FxLatestPoint[]>("/snapshots/latest/fx"),
  });

  const repairMutation = useMutation({
    mutationFn: async ({ quoteId, payload }: { quoteId: string; payload: Partial<ExtractedQuote> }) =>
      fetchApi<QuoteState>(`/quotes/${quoteId}/repair`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  });

  const runAnalysisMutation = useMutation({
    mutationFn: async () => {
      const editedQuotes = Object.values(localQuotes);
      await Promise.all(
        editedQuotes.map((quote) =>
          repairMutation.mutateAsync({
            quoteId: quote.quote_id,
            payload: {
              supplier_name: quote.supplier_name,
              origin_port_or_country: quote.origin_port_or_country,
              incoterm: quote.incoterm,
              unit_price: quote.unit_price,
              currency: quote.currency,
              moq: quote.moq,
              lead_time_days: quote.lead_time_days,
              payment_terms: quote.payment_terms,
              extraction_confidence: 1.0,
            },
          }),
        ),
      );

      return fetchApi<AnalysisRunResponse>("/analysis/run", {
        method: "POST",
        body: JSON.stringify({
          quote_ids: quoteIds,
          quantity_mt: quantityMt,
          urgency,
          hedge_preference: hedgePreference,
        }),
      });
    },
    onSuccess: (payload) => {
      router.push(`/analysis/${payload.run_id}`);
    },
  });

  const handleFieldChange = (quoteId: string, field: keyof ExtractedQuote, value: string) => {
    setQuoteOverrides((prev) => {
      const existing = prev[quoteId];
      const baseQuote = localQuotes[quoteId];
      if (!existing && !baseQuote) {
        return prev;
      }
      const nextValue =
        field === "unit_price" || field === "moq" || field === "lead_time_days"
          ? value === ""
            ? null
            : Number(value)
          : value;
      return {
        ...prev,
        [quoteId]: {
          ...(existing ?? baseQuote),
          [field]: nextValue,
          extraction_confidence: 1.0,
        },
      };
    });
  };

  const inputField = ({
    label,
    value,
    confidence,
    onChange,
    type = "text",
  }: {
    label: string;
    value: string | number | null;
    confidence: number | null;
    onChange: (nextValue: string) => void;
    type?: "text" | "number";
  }) => {
    const isLowConfidence = confidence !== null && confidence < 0.7;

    return (
      <div className="flex flex-col gap-1.5">
        <label className="text-body-sm font-semibold text-on-background">{label}</label>
        <div className="relative">
          <input
            type={type}
            value={value ?? ""}
            onChange={(event) => onChange(event.target.value)}
            className={[
              "w-full border rounded p-2 text-body-base focus:ring-1 focus:outline-none transition-all",
              isLowConfidence 
                ? "border-[#ba1a1a] focus:border-[#ba1a1a] focus:ring-[#ba1a1a]" 
                : "border-outline-variant focus:border-[#004aad] focus:ring-[#004aad]"
            ].join(" ")}
          />
          {isLowConfidence && (
            <span className="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-[#ba1a1a] text-sm">warning</span>
          )}
        </div>
      </div>
    );
  };

  const quoteCards = quotesQuery.data?.map((state, index) => {
    const quote = state.extracted_quote ? localQuotes[state.extracted_quote.quote_id] ?? state.extracted_quote : null;
    if (!quote) {
      return null;
    }

    const countryCode = inferCountryCode(quote.origin_port_or_country);

    return (
      <div key={quote.quote_id} className="bg-white border border-outline-variant p-card-padding rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.04)] mb-stack-md">
        <div className="flex justify-between items-center mb-stack-lg pb-stack-sm border-b border-slate-100">
          <h3 className="font-h2 text-h2 text-on-background flex items-center gap-2">
            <span className="material-symbols-outlined text-[#004aad]">fact_check</span> Data Extraction Verification - Quote {index + 1}
          </h3>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 bg-[#d9e2ff] text-[#001945] rounded font-label-caps text-[10px] tracking-widest uppercase">AI Extracted</span>
            <span className="px-2.5 py-1 bg-surface-container-high text-on-surface rounded font-label-caps text-[10px] tracking-widest uppercase">{FLAG_BY_COUNTRY[countryCode] ?? "OT"}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-gutter gap-y-stack-md">
          {inputField({
            label: "Supplier Name",
            value: quote.supplier_name,
            confidence: quote.extraction_confidence,
            onChange: (nextValue) => handleFieldChange(quote.quote_id, "supplier_name", nextValue),
          })}
          {inputField({
            label: "Origin Port/Country",
            value: quote.origin_port_or_country,
            confidence: quote.extraction_confidence,
            onChange: (nextValue) => handleFieldChange(quote.quote_id, "origin_port_or_country", nextValue),
          })}
          {inputField({
            label: "Incoterm",
            value: quote.incoterm,
            confidence: quote.extraction_confidence,
            onChange: (nextValue) => handleFieldChange(quote.quote_id, "incoterm", nextValue),
          })}
          {inputField({
            label: "Currency",
            value: quote.currency,
            confidence: quote.extraction_confidence,
            onChange: (nextValue) => handleFieldChange(quote.quote_id, "currency", nextValue),
          })}
          {inputField({
            label: "Unit Price",
            value: quote.unit_price,
            confidence: quote.extraction_confidence,
            onChange: (nextValue) => handleFieldChange(quote.quote_id, "unit_price", nextValue),
            type: "number",
          })}
          {inputField({
            label: "MOQ",
            value: quote.moq,
            confidence: quote.extraction_confidence,
            onChange: (nextValue) => handleFieldChange(quote.quote_id, "moq", nextValue),
            type: "number",
          })}
          {inputField({
            label: "Lead Time (Days)",
            value: quote.lead_time_days,
            confidence: quote.extraction_confidence,
            onChange: (nextValue) => handleFieldChange(quote.quote_id, "lead_time_days", nextValue),
            type: "number",
          })}
        </div>
      </div>
    );
  });

  return (
    <AnalysisShell
      currentStep="review"
      title="Stage 2: Validation Review"
      subtitle="Correct low-confidence fields before running deterministic landed-cost ranking."
      actions={
        <>
          <div className="hidden sm:flex rounded border border-outline-variant bg-white px-3 py-1.5 text-[11px] font-bold tracking-widest text-secondary uppercase items-center gap-2">
            <span className="material-symbols-outlined text-sm">inventory_2</span> Quantity: {quantityMt} MT
          </div>
          <select
            value={hedgePreference}
            onChange={(event) => setHedgePreference(event.target.value)}
            className="hidden sm:flex h-[34px] rounded border border-outline-variant bg-white px-3 text-[11px] font-bold tracking-widest text-secondary uppercase items-center gap-2 outline-none"
          >
            <option value="balance">Balanced Hedge</option>
            <option value="conservative">Conservative</option>
            <option value="aggressive">Aggressive</option>
          </select>
          <button
            type="button"
            onClick={() => runAnalysisMutation.mutate()}
            disabled={runAnalysisMutation.isPending || quoteIds.length === 0 || quotesQuery.isLoading}
            className="px-6 py-2 bg-[#004aad] text-white font-semibold text-body-sm rounded hover:opacity-90 transition-opacity flex items-center gap-2 shadow-sm disabled:cursor-not-allowed disabled:opacity-50"
          >
            {runAnalysisMutation.isPending ? "Starting analysis..." : "Confirm All & Proceed"} <span className="material-symbols-outlined text-base">arrow_forward</span>
          </button>
        </>
      }
    >
      <div className="grid grid-cols-12 gap-gutter">
        {/* Left Column: Context / Quotes */}
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-gutter">
          {quotesQuery.error ? (
            <div className="rounded border border-[#ba1a1a] bg-white p-5 text-sm text-[#ba1a1a]">
              {(quotesQuery.error as Error).message}
            </div>
          ) : null}

          {quotesQuery.isLoading ? (
            Array.from({ length: Math.max(quoteIds.length, 1) }, (_, index) => (
              <div key={index} className="h-[200px] rounded-lg border border-outline-variant bg-white animate-pulse" />
            ))
          ) : (
            quoteCards
          )}
        </div>

        {/* Right Column: Execution Checks & Macro Context */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-gutter">
          <div className="bg-white border border-outline-variant p-card-padding rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
            <h3 className="text-label-caps font-label-caps text-secondary uppercase mb-stack-md flex items-center gap-2">
              <span className="material-symbols-outlined text-[#004aad]">currency_exchange</span> Live Macro Rates
            </h3>
            <div className="space-y-stack-sm">
              {fxQuery.isLoading ? (
                <div className="text-sm text-secondary">Loading latest FX rates...</div>
              ) : fxQuery.data?.length ? (
                fxQuery.data.map((fxPoint) => (
                  <div key={fxPoint.pair} className="flex justify-between items-center p-3 border border-outline-variant rounded bg-surface-container-lowest">
                    <span className="text-body-sm font-semibold text-secondary">{fxPoint.pair}</span>
                    <span className="font-data-mono font-medium text-on-background">{fxPoint.close.toFixed(4)}</span>
                  </div>
                ))
              ) : (
                <div className="p-3 border border-outline-variant rounded bg-surface-container-lowest text-sm text-secondary">
                  FX snapshots unavailable.
                </div>
              )}
            </div>
          </div>
          
          <div className="bg-[#f7f9fb] border border-outline-variant p-card-padding rounded-lg">
             <div className="flex gap-2 items-start">
               <span className="material-symbols-outlined text-[#004aad] text-lg">info</span>
               <p className="text-[11px] leading-relaxed text-secondary font-medium">
                 Only valid or repaired quotes move into ranking. Invalid out-of-scope quotes are filtered out by the backend.
               </p>
             </div>
          </div>
        </div>
      </div>
    </AnalysisShell>
  );
}

export default function ReviewPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-surface-container-lowest p-6 text-secondary flex items-center justify-center"><span className="material-symbols-outlined animate-spin mr-2">refresh</span>Loading review context...</div>}>
      <ReviewPageContent />
    </Suspense>
  );
}
