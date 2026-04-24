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
      <label className="flex flex-col gap-2">
        <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-secondary-text">{label}</span>
        <input
          type={type}
          value={value ?? ""}
          onChange={(event) => onChange(event.target.value)}
          className={[
            "h-11 rounded-xl border bg-background px-4 text-sm text-foreground outline-none transition focus:border-primary",
            isLowConfidence ? "border-[var(--color-warning)]" : "border-border",
          ].join(" ")}
        />
        {isLowConfidence ? (
          <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--color-warning)]">
            Please verify
          </span>
        ) : null}
      </label>
    );
  };

  const quoteCards = quotesQuery.data?.map((state) => {
    const quote = state.extracted_quote ? localQuotes[state.extracted_quote.quote_id] ?? state.extracted_quote : null;
    if (!quote) {
      return null;
    }

    const countryCode = inferCountryCode(quote.origin_port_or_country);

    return (
      <section key={quote.quote_id} className="overflow-hidden rounded-2xl border border-border bg-surface">
        <div className="border-b border-border px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-border bg-background text-xs font-bold uppercase tracking-[0.18em] text-primary">
              {FLAG_BY_COUNTRY[countryCode] ?? "OT"}
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">{quote.supplier_name ?? "Unknown supplier"}</h3>
              <p className="text-sm text-secondary-text">Quote ID {quote.quote_id.slice(0, 8)}</p>
            </div>
          </div>
        </div>
        <div className="space-y-4 p-5">
          {inputField({
            label: "Supplier name",
            value: quote.supplier_name,
            confidence: quote.extraction_confidence,
            onChange: (nextValue) => handleFieldChange(quote.quote_id, "supplier_name", nextValue),
          })}
          <div className="grid gap-4 md:grid-cols-2">
            {inputField({
              label: "Currency",
              value: quote.currency,
              confidence: quote.extraction_confidence,
              onChange: (nextValue) => handleFieldChange(quote.quote_id, "currency", nextValue),
            })}
            {inputField({
              label: "Unit price",
              value: quote.unit_price,
              confidence: quote.extraction_confidence,
              onChange: (nextValue) => handleFieldChange(quote.quote_id, "unit_price", nextValue),
              type: "number",
            })}
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {inputField({
              label: "MOQ",
              value: quote.moq,
              confidence: quote.extraction_confidence,
              onChange: (nextValue) => handleFieldChange(quote.quote_id, "moq", nextValue),
              type: "number",
            })}
            {inputField({
              label: "Lead time (days)",
              value: quote.lead_time_days,
              confidence: quote.extraction_confidence,
              onChange: (nextValue) => handleFieldChange(quote.quote_id, "lead_time_days", nextValue),
              type: "number",
            })}
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {inputField({
              label: "Incoterm",
              value: quote.incoterm,
              confidence: quote.extraction_confidence,
              onChange: (nextValue) => handleFieldChange(quote.quote_id, "incoterm", nextValue),
            })}
            {inputField({
              label: "Origin",
              value: quote.origin_port_or_country,
              confidence: quote.extraction_confidence,
              onChange: (nextValue) => handleFieldChange(quote.quote_id, "origin_port_or_country", nextValue),
            })}
          </div>
        </div>
      </section>
    );
  });

  return (
    <AnalysisShell
      currentStep="review"
      title="Review extracted quote data"
      subtitle="Correct low-confidence fields before running deterministic landed-cost ranking and the bounded reasoning layer."
      actions={
        <>
          <div className="rounded-full border border-border bg-surface px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-secondary-text">
            Quantity {quantityMt} MT
          </div>
          <div className="rounded-full border border-border bg-surface px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-secondary-text">
            Urgency {urgency}
          </div>
          <select
            value={hedgePreference}
            onChange={(event) => setHedgePreference(event.target.value)}
            className="h-10 rounded-full border border-border bg-surface px-4 text-sm text-foreground outline-none transition focus:border-primary"
          >
            <option value="balance">Balanced hedge</option>
            <option value="conservative">Conservative hedge</option>
            <option value="aggressive">Aggressive hedge</option>
          </select>
          <button
            type="button"
            onClick={() => runAnalysisMutation.mutate()}
            disabled={runAnalysisMutation.isPending || quoteIds.length === 0 || quotesQuery.isLoading}
            className="inline-flex h-11 items-center justify-center rounded-full bg-primary px-6 text-sm font-semibold text-background transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {runAnalysisMutation.isPending ? "Starting analysis..." : "Run analysis"}
          </button>
        </>
      }
    >
      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="grid gap-6">
          {quotesQuery.error ? (
            <div className="rounded-2xl border border-[var(--color-warning)] bg-surface p-5 text-sm text-[var(--color-warning)]">
              {(quotesQuery.error as Error).message}
            </div>
          ) : null}

          {quotesQuery.isLoading ? (
            Array.from({ length: Math.max(quoteIds.length, 1) }, (_, index) => (
              <div key={index} className="h-[320px] rounded-2xl border border-border bg-surface" />
            ))
          ) : (
            quoteCards
          )}
        </div>

        <div className="space-y-6">
          <section className="rounded-2xl border border-border bg-surface">
            <div className="border-b border-border px-5 py-4">
              <h2 className="text-sm font-bold uppercase tracking-[0.18em] text-secondary-text">Execution checks</h2>
            </div>
            <div className="space-y-4 p-5 text-sm text-secondary-text">
              <div className="rounded-xl border border-border bg-background p-4">
                Only valid or repaired quotes move into ranking. Invalid out-of-scope quotes are filtered out by the backend.
              </div>
              <div className="rounded-xl border border-border bg-background p-4">
                The run button calls <code>/analysis/run</code>, then Step 3 loads{" "}
                <code>analysis/{"{run_id}"}</code> before redirecting to decision.
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-border bg-surface">
            <div className="border-b border-border px-5 py-4">
              <h2 className="text-sm font-bold uppercase tracking-[0.18em] text-secondary-text">Macro context</h2>
            </div>
            <div className="space-y-3 p-5">
              {fxQuery.isLoading ? (
                <div className="text-sm text-secondary-text">Loading latest FX rates...</div>
              ) : fxQuery.data?.length ? (
                fxQuery.data.map((fxPoint) => (
                  <div key={fxPoint.pair} className="rounded-xl border border-border bg-background p-4">
                    <div className="text-[11px] font-bold uppercase tracking-[0.18em] text-secondary-text">{fxPoint.pair}</div>
                    <div className="mt-2 text-2xl font-semibold text-foreground">{fxPoint.close.toFixed(4)}</div>
                    <div className="mt-1 text-xs text-secondary-text">{fxPoint.as_of ?? "latest"}</div>
                  </div>
                ))
              ) : (
                <div className="rounded-xl border border-border bg-background p-4 text-sm text-secondary-text">
                  FX snapshots are not available yet. The backend will fall back to deterministic defaults if needed.
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </AnalysisShell>
  );
}

export default function ReviewPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background p-6 text-secondary-text">Loading review context...</div>}>
      <ReviewPageContent />
    </Suspense>
  );
}
