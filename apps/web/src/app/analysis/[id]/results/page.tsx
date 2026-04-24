"use client";

import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { pdf } from "@react-pdf/renderer";
import { Download, Lock, ShieldCheck, Truck, WalletCards, Zap } from "lucide-react";
import { useParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";

import { AnalysisShell } from "@/components/analysis-shell";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchApi } from "@/lib/api";
import { AnalysisResultPayload, BankInstructionDraft, HedgeScenarioResult } from "@/lib/types";

import { ForwardContractPDF } from "./components/ForwardContractPDF";
import { FxFanChart } from "./components/FxFanChart";
import { HedgeSlider } from "./components/HedgeSlider";
import { ReasoningPanel } from "./components/ReasoningPanel";
import { SupplierCard } from "./components/SupplierCard";

function winnerCurrencyPair(analysis?: AnalysisResultPayload): string | null {
  const winner = analysis?.ranked_quotes[0];
  if (!winner?.quote.currency) {
    return null;
  }
  return `${winner.quote.currency}MYR`;
}

function formatMyr(value: number) {
  return `RM ${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function chartDirection(data?: HedgeScenarioResult | AnalysisResultPayload["selected_scenario"]) {
  if (!data?.p50_envelope?.length) {
    return "stable";
  }
  const start = data.p50_envelope[0];
  const end = data.p50_envelope[data.p50_envelope.length - 1];
  if (end <= start * 0.985) {
    return "trending lower";
  }
  if (end >= start * 1.015) {
    return "trending higher";
  }
  return "stable";
}

async function downloadInstructionPdf(draft: BankInstructionDraft) {
  const blob = await pdf(<ForwardContractPDF draft={draft} />).toBlob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "lintasniaga-forward-contract-instruction.pdf";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export default function ResultsPage() {
  const params = useParams<{ id: string }>();
  const runId = params.id;
  const [hedgeRatio, setHedgeRatio] = useState<number | null>(null);
  const [pdfStatus, setPdfStatus] = useState<string | null>(null);

  const analysisQuery = useQuery({
    queryKey: ["analysis-result", runId],
    enabled: Boolean(runId),
    queryFn: () => fetchApi<AnalysisResultPayload>(`/analysis/${runId}`),
  });

  const hedgeMutation = useMutation({
    mutationFn: async (ratio: number) =>
      fetchApi<HedgeScenarioResult>(`/analysis/${runId}/hedge-simulate`, {
        method: "POST",
        body: JSON.stringify({ hedge_ratio: ratio }),
      }),
  });

  const bankDraftMutation = useMutation({
    mutationFn: async (ratio: number) =>
      fetchApi<BankInstructionDraft>(`/analysis/${runId}/bank-instruction-draft`, {
        method: "POST",
        body: JSON.stringify({ hedge_ratio: ratio }),
      }),
    onSuccess: async (draft) => {
      await downloadInstructionPdf(draft);
      setPdfStatus("Forward contract instruction PDF generated for Maybank / CIMB workflow.");
    },
    onError: (error) => {
      setPdfStatus(error instanceof Error ? error.message : "PDF generation failed.");
    },
  });

  const { data: hedgeData, mutate: mutateHedge } = hedgeMutation;
  const analysis = analysisQuery.data;
  const effectiveHedgeRatio = hedgeRatio ?? Math.round(analysis?.recommendation.hedge_pct ?? 50);

  useEffect(() => {
    if (!analysisQuery.data || !runId) {
      return;
    }
    const handle = window.setTimeout(() => {
      mutateHedge(effectiveHedgeRatio);
    }, 300);
    return () => window.clearTimeout(handle);
  }, [analysisQuery.data, effectiveHedgeRatio, mutateHedge, runId]);

  const recommendedQuoteId = analysis?.recommendation.recommended_quote_id;
  const savingsVsNextBest = useMemo(() => {
    if (!analysis || analysis.ranked_quotes.length < 2) {
      return 0;
    }
    const ranked = analysis.ranked_quotes
      .slice()
      .sort((left, right) => left.cost_result.total_landed_p50 - right.cost_result.total_landed_p50);
    return ranked[1].cost_result.total_landed_p50 - ranked[0].cost_result.total_landed_p50;
  }, [analysis]);

  const pair = winnerCurrencyPair(analysis);
  const activeScenario = hedgeData ?? analysis?.hedge_simulation ?? analysis?.selected_scenario ?? null;
  const expectedCost = activeScenario?.p50_envelope?.at(-1) ?? analysis?.recommendation.expected_landed_cost_myr ?? 0;
  const p90Cost = activeScenario?.p90_envelope?.at(-1) ?? analysis?.ranked_quotes[0]?.cost_result.total_landed_p90 ?? 0;
  const riskWidth = activeScenario?.risk_width_envelope?.at(-1) ?? Math.max(0, p90Cost - expectedCost);
  const avgCost =
    analysis?.ranked_quotes.length
      ? analysis.ranked_quotes.reduce((sum, item) => sum + item.cost_result.total_landed_p50, 0) /
        analysis.ranked_quotes.length
      : 0;
  const direction = chartDirection(activeScenario);

  return (
    <AnalysisShell
      currentStep="decision"
      title="Decision workspace"
      subtitle="30-day landed-cost Monte Carlo across tariff, freight, FX, oil, weather, holidays, macro, news, and PP resin benchmark."
      actions={
        analysis?.recommendation ? (
          <div className="rounded-full border border-primary/30 bg-primary/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-primary">
            {analysis.recommendation.mode === "single_quote" ? "Single quote mode" : "Comparison mode"}
          </div>
        ) : undefined
      }
    >
      {analysisQuery.error ? (
        <div className="rounded-xl border border-[var(--color-warning)] bg-surface p-4 text-sm text-[var(--color-warning)]">
          {(analysisQuery.error as Error).message}
        </div>
      ) : null}

      <div className="mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard icon={<Zap size={16} />} label={`Current FX (${pair ?? "N/A"})`} value={pair ? `${analysis?.fx_simulations[pair]?.current_spot?.toFixed(4) ?? "-"}` : "-"} helper="Spot used for locked hedge leg" />
        <KpiCard icon={<Truck size={16} />} label="Avg Landed Cost" value={formatMyr(avgCost)} helper="Supplier p50 average" />
        <KpiCard icon={<ShieldCheck size={16} />} label="P90 Risk Exposure" value={formatMyr(Math.max(0, p90Cost - expectedCost))} helper={`Fan width: ${formatMyr(riskWidth)}`} warning={Boolean(activeScenario?.p90_margin_wipeout_flag)} />
        <KpiCard icon={<WalletCards size={16} />} label="Hedge Ratio" value={`${effectiveHedgeRatio}%`} helper={`Curve is ${direction}`} />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_330px]">
        <div className="rounded-xl border border-border bg-surface p-5">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-foreground">
                30-Day Landed Cost Forecast
              </h2>
              <p className="mt-1 text-xs text-secondary-text">
                Deterministic 2,000-path simulation. Hedge changes reuse the same shocks, so the chart narrows without rerolling.
              </p>
            </div>
            <div className="rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
              D0 to D30
            </div>
          </div>

          {analysisQuery.isLoading ? <Skeleton className="h-[320px] w-full bg-border" /> : null}
          {!analysisQuery.isLoading && activeScenario ? (
            <FxFanChart data={activeScenario} valuePrefix="RM " />
          ) : null}
          {!analysisQuery.isLoading && !activeScenario ? (
            <div className="rounded-lg border border-border bg-[var(--color-surface-elevated)] p-4 text-sm text-secondary-text">
              Landed-cost scenario is not available. Run analysis again after market snapshots are loaded.
            </div>
          ) : null}

          <div className="mt-4 grid gap-3 text-xs text-secondary-text md:grid-cols-3">
            <div className="rounded-lg border border-border bg-[var(--color-surface-elevated)] p-3">
              <span className="block uppercase tracking-wider">P10 optimistic</span>
              <span className="font-mono text-foreground">{formatMyr(activeScenario?.p10_envelope?.at(-1) ?? 0)}</span>
            </div>
            <div className="rounded-lg border border-primary/30 bg-primary/10 p-3">
              <span className="block uppercase tracking-wider">P50 expected</span>
              <span className="font-mono text-primary">{formatMyr(expectedCost)}</span>
            </div>
            <div className="rounded-lg border border-[var(--color-warning)]/40 bg-[var(--color-warning)]/10 p-3">
              <span className="block uppercase tracking-wider">P90 stress</span>
              <span className="font-mono text-[var(--color-warning)]">{formatMyr(p90Cost)}</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-primary/20 bg-[linear-gradient(180deg,rgba(0,245,212,0.10),rgba(18,19,26,0.95))] p-5">
          <ReasoningPanel
            isLoading={analysisQuery.isLoading}
            recommendation={analysis?.recommendation}
            traceUrl={analysis?.trace_url}
          />

          {analysisQuery.isLoading ? (
            <Skeleton className="mt-5 h-[140px] w-full bg-border" />
          ) : (
            <HedgeSlider
              hedgeRatio={effectiveHedgeRatio}
              onHedgeChange={setHedgeRatio}
              expectedLandedCost={expectedCost}
            />
          )}

          <div className="mt-4 space-y-3">
            <button
              type="button"
              onClick={() => bankDraftMutation.mutate(effectiveHedgeRatio)}
              disabled={!analysis || bankDraftMutation.isPending}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 text-sm font-bold text-background transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Download size={16} />
              {bankDraftMutation.isPending ? "Generating..." : "Generate Bank Instruction (Maybank / CIMB)"}
            </button>
            <button
              type="button"
              disabled
              title="V2 roadmap: direct API execution for API-first fintech partners."
              className="flex w-full cursor-not-allowed items-center justify-center gap-2 rounded-lg border border-border bg-background/20 px-4 py-3 text-sm font-semibold text-secondary-text opacity-70"
            >
              <Lock size={16} />
              Execute via WorldFirst API (Coming Soon)
            </button>
            {pdfStatus ? <p className="text-xs text-primary">{pdfStatus}</p> : null}
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_330px]">
        <div className="rounded-xl border border-border bg-surface p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-sm font-bold uppercase tracking-wider text-foreground">
              {analysis?.recommendation.mode === "single_quote" ? "Single Quote Evaluation" : "Active Procurement Quotes"}
            </h2>
            <div className="text-xs text-secondary-text">Quote-vs-PP-market badges are live from SunSirs snapshots.</div>
          </div>

          {analysisQuery.isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-[200px] w-full rounded-xl bg-border" />
              <Skeleton className="h-[150px] w-full rounded-xl bg-border" />
            </div>
          ) : null}

          <div className="grid gap-4 lg:grid-cols-2">
            {!analysisQuery.isLoading
              ? analysis?.ranked_quotes.map((rankedQuote) => (
                  <SupplierCard
                    key={rankedQuote.quote.quote_id}
                    rankedQuote={rankedQuote}
                    isRecommended={rankedQuote.quote.quote_id === recommendedQuoteId}
                    timingAdvice={
                      rankedQuote.quote.quote_id === recommendedQuoteId ? analysis.recommendation.timing : undefined
                    }
                    hedgeRec={
                      rankedQuote.quote.quote_id === recommendedQuoteId ? analysis.recommendation.hedge_pct : undefined
                    }
                    whyNotReason={analysis?.recommendation.why_not_others[rankedQuote.quote.quote_id]}
                    singleQuoteMode={analysis?.recommendation.mode === "single_quote"}
                    evaluationLabel={analysis?.recommendation.evaluation_label}
                    savingsVsNextBest={savingsVsNextBest}
                  />
                ))
              : null}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-surface p-5">
          <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-foreground">9-Aspect Risk Drivers</h2>
          {analysis?.risk_driver_breakdown ? (
            <div className="space-y-3">
              {Object.entries(analysis.risk_driver_breakdown)
                .filter(([key]) => key !== "notes")
                .map(([key, value]) => (
                  <div key={key}>
                    <div className="mb-1 flex justify-between text-xs uppercase tracking-wider text-secondary-text">
                      <span>{key.replaceAll("_", " ")}</span>
                      <span>{Math.round(Number(value) * 100)}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-background">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${Math.min(100, Math.max(0, Number(value) * 100))}%` }}
                      />
                    </div>
                  </div>
                ))}
            </div>
          ) : (
            <p className="text-sm text-secondary-text">Risk driver breakdown is not available yet.</p>
          )}
        </div>
      </div>
    </AnalysisShell>
  );
}

function KpiCard({
  icon,
  label,
  value,
  helper,
  warning = false,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  helper: string;
  warning?: boolean;
}) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <div className="mb-4 flex items-center justify-between text-secondary-text">
        <span className="text-[11px] font-bold uppercase tracking-[0.16em]">{label}</span>
        <span className={warning ? "text-[var(--color-warning)]" : "text-secondary-text"}>{icon}</span>
      </div>
      <div className="font-mono text-3xl font-semibold text-foreground">{value}</div>
      <div className={warning ? "mt-2 text-xs text-[var(--color-warning)]" : "mt-2 text-xs text-primary"}>
        {helper}
      </div>
    </div>
  );
}
