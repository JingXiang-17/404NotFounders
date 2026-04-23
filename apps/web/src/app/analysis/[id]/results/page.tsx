"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";

import { AnalysisShell } from "@/components/analysis-shell";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchApi } from "@/lib/api";
import { AnalysisResultPayload, HedgeScenarioResult } from "@/lib/types";

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

export default function ResultsPage() {
  const params = useParams<{ id: string }>();
  const runId = params.id;
  const [hedgeRatio, setHedgeRatio] = useState(50);

  const analysisQuery = useQuery({
    queryKey: ["analysis-result", runId],
    enabled: Boolean(runId),
    queryFn: () => fetchApi<AnalysisResultPayload>(`/analysis/${runId}`),
  });

  useEffect(() => {
    if (analysisQuery.data) {
      setHedgeRatio(Math.round(analysisQuery.data.recommendation.hedge_pct));
    }
  }, [analysisQuery.data]);

  const hedgeMutation = useMutation({
    mutationFn: async (ratio: number) =>
      fetchApi<HedgeScenarioResult>(`/analysis/${runId}/hedge-simulate`, {
        method: "POST",
        body: JSON.stringify({ hedge_ratio: ratio }),
      }),
  });

  useEffect(() => {
    if (!analysisQuery.data || !runId) {
      return;
    }
    const handle = window.setTimeout(() => {
      hedgeMutation.mutate(hedgeRatio);
    }, 300);
    return () => window.clearTimeout(handle);
  }, [analysisQuery.data, hedgeRatio, runId]);

  const analysis = analysisQuery.data;
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
  const fxSimulation = pair ? analysis?.fx_simulations[pair] ?? analysis?.fx_simulations.USDMYR : analysis?.fx_simulations.USDMYR;
  const displayedCost = hedgeMutation.data?.adjusted_p50 ?? analysis?.recommendation.expected_landed_cost_myr ?? 0;

  return (
    <AnalysisShell
      currentStep="decision"
      title="Decision workspace"
      subtitle="Review deterministic costs, FX scenarios, hedge sensitivity, and bounded AI reasoning before sending a supplier recommendation downstream."
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

      <div className="flex flex-col gap-6 lg:flex-row">
        <div className="flex w-full flex-col gap-6 lg:w-[45%]">
          <div className="rounded-xl border border-border bg-surface p-5">
            <h2 className="mb-2 text-sm font-bold uppercase tracking-wider text-foreground">
              FX Risk Simulation ({pair ?? "USDMYR"})
            </h2>
            <p className="mb-4 text-xs text-secondary-text">90-day p10, p50, and p90 scenario envelopes</p>

            {analysisQuery.isLoading ? <Skeleton className="h-[250px] w-full bg-border" /> : null}
            {!analysisQuery.isLoading && fxSimulation ? <FxFanChart data={fxSimulation} /> : null}
            {!analysisQuery.isLoading && !fxSimulation ? (
              <div className="rounded-lg border border-border bg-[var(--color-surface-elevated)] p-4 text-sm text-secondary-text">
                FX simulation not available for this currency yet.
              </div>
            ) : null}

            {analysisQuery.isLoading ? (
              <Skeleton className="mt-6 h-[100px] w-full bg-border" />
            ) : (
              <HedgeSlider
                hedgeRatio={hedgeRatio}
                onHedgeChange={setHedgeRatio}
                expectedLandedCost={displayedCost}
              />
            )}
          </div>
        </div>

        <div className="flex w-full flex-col gap-4 lg:w-[35%]">
          <h2 className="mb-1 text-sm font-bold uppercase tracking-wider text-foreground">
            {analysis?.recommendation.mode === "single_quote" ? "Single Quote Evaluation" : "Supplier Ranking"}
          </h2>

          {analysisQuery.isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-[200px] w-full rounded-xl bg-border" />
              <Skeleton className="h-[150px] w-full rounded-xl bg-border" />
            </div>
          ) : null}

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

        <div className="w-full lg:w-[20%]">
          <div className="h-full rounded-xl border border-border bg-surface p-5">
            <ReasoningPanel
              isLoading={analysisQuery.isLoading}
              recommendation={analysis?.recommendation}
              traceUrl={analysis?.trace_url}
            />
          </div>
        </div>
      </div>
    </AnalysisShell>
  );
}
