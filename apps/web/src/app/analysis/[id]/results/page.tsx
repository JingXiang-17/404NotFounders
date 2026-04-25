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
import { AnalysisResultPayload, BankInstructionDraft, HedgeScenarioResult, NewsEvent, SnapshotEnvelope } from "@/lib/types";

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

interface WeatherPortRisk {
  port_code?: string;
  port_name?: string;
  country_code?: string;
  max_risk_score?: number;
  worst_slot_date?: string;
  raw_weather_summary?: string;
  alert_present?: boolean;
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
  const latestNewsQuery = useQuery({
    queryKey: ["latest-news-snapshot"],
    queryFn: () => fetchApi<SnapshotEnvelope<NewsEvent> | null>("/snapshots/latest/news"),
  });
  const latestWeatherQuery = useQuery({
    queryKey: ["latest-weather-snapshot"],
    queryFn: () => fetchApi<SnapshotEnvelope<WeatherPortRisk> | null>("/snapshots/latest/weather"),
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
  const decisionGridClass = "grid gap-5 xl:grid-cols-[minmax(0,1fr)_330px]";
  const latestNewsEvents = analysis?.top_news_events?.length
    ? analysis.top_news_events
    : latestNewsQuery.data?.data ?? [];
  const latestWeatherRisks = latestWeatherQuery.data?.data ?? [];

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

      <div className={decisionGridClass}>
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
            <div className="flex flex-col items-end gap-2">
              <div className="rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                D0 to D30
              </div>
              <div className="flex items-center gap-3 text-[10px] uppercase tracking-wider text-secondary-text">
                <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-[rgba(0,245,212,0.8)]"></span> P10 (Optimistic)</span>
                <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-primary"></span> P50 (Expected)</span>
                <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-[rgba(255,107,107,0.8)]"></span> P90 (Stress)</span>
              </div>
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

          <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(280px,420px)_minmax(0,1fr)]">
            {analysisQuery.isLoading ? (
              <Skeleton className="h-[132px] w-full bg-border" />
            ) : (
              <HedgeSlider
                hedgeRatio={effectiveHedgeRatio}
                onHedgeChange={setHedgeRatio}
                expectedLandedCost={expectedCost}
              />
            )}

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
              <button
                type="button"
                onClick={() => bankDraftMutation.mutate(effectiveHedgeRatio)}
                disabled={!analysis || bankDraftMutation.isPending}
                className="flex min-h-[68px] w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 text-sm font-bold text-background transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Download size={16} />
                {bankDraftMutation.isPending ? "Generating..." : "Generate Bank Instruction (Maybank / CIMB)"}
              </button>
              <button
                type="button"
                disabled
                title="V2 roadmap: direct API execution for API-first fintech partners."
                className="flex min-h-[68px] w-full cursor-not-allowed items-center justify-center gap-2 rounded-lg border border-border bg-background/20 px-4 py-3 text-sm font-semibold text-secondary-text opacity-70"
              >
                <Lock size={16} />
                Execute via WorldFirst API (Coming Soon)
              </button>
              {pdfStatus ? <p className="text-xs text-primary sm:col-span-2 lg:col-span-1">{pdfStatus}</p> : null}
            </div>
          </div>
        </div>

        <RiskDriversPanel
          analysis={analysis}
          latestNewsEvents={latestNewsEvents}
          latestWeatherRisks={latestWeatherRisks}
        />
      </div>

      <div className={`mt-5 ${decisionGridClass}`}>
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

        <div className="rounded-xl border border-primary/20 bg-[linear-gradient(180deg,rgba(0,245,212,0.10),rgba(18,19,26,0.95))] p-5">
          <ReasoningPanel
            isLoading={analysisQuery.isLoading}
            recommendation={analysis?.recommendation}
            traceUrl={analysis?.trace_url}
          />
        </div>
      </div>
    </AnalysisShell>
  );
}

function RiskDriversPanel({
  analysis,
  latestNewsEvents,
  latestWeatherRisks,
}: {
  analysis?: AnalysisResultPayload;
  latestNewsEvents: NewsEvent[];
  latestWeatherRisks: WeatherPortRisk[];
}) {
  const risk = analysis?.risk_driver_breakdown;
  const rows = risk ? buildRiskRows(analysis, latestNewsEvents, latestWeatherRisks) : [];
  const highlightedRows = rows.filter((row) => row.score >= 0.6 && row.hasConcreteEvidence).slice(0, 4);

  return (
    <div className="max-h-[640px] overflow-hidden rounded-xl border border-border bg-surface p-5">
      <h2 className="text-sm font-bold uppercase tracking-wider text-foreground">Risk Drivers</h2>

      {risk ? (
        <div className="mt-4 max-h-[545px] space-y-4 overflow-y-auto pr-1">
          {highlightedRows.length ? highlightedRows.map((row) => (
            <div key={`insight-${row.key}`} className="rounded-lg border border-border bg-[var(--color-surface-elevated)] p-3">
              <div className="mb-2 flex items-center justify-between gap-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">{row.label}</h3>
              </div>
              <p className="text-xs leading-relaxed text-secondary-text">{row.evidence}</p>
              <p className="mt-3 rounded-md border border-border bg-background/40 p-2 text-xs leading-relaxed text-secondary-text">
                {row.effect}
              </p>
              {row.news.length ? (
                <div className="mt-3 space-y-2">
                  {row.news.map((item) => (
                    <a
                      key={`${row.key}-${item.title}-${item.url}`}
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block rounded-md border border-border bg-background/40 p-2 text-xs transition hover:border-primary/40"
                    >
                      <span className="block font-medium text-foreground">{item.title || "Market event"}</span>
                      <span className="mt-1 block text-[11px] text-secondary-text">
                        {item.source || "News"}
                      </span>
                    </a>
                  ))}
                </div>
              ) : null}
            </div>
          )) : (
            <p className="rounded-lg border border-border bg-[var(--color-surface-elevated)] p-3 text-xs leading-relaxed text-secondary-text">
              No high-impact live driver has concrete evidence in this run. This panel stays quiet unless a real snapshot, article, port forecast, or price move explains the risk.
            </p>
          )}
        </div>
      ) : (
        <p className="mt-4 text-sm text-secondary-text">Risk driver analysis is not available yet.</p>
      )}
    </div>
  );
}

function buildRiskRows(
  analysis: AnalysisResultPayload,
  latestNewsEvents: NewsEvent[],
  latestWeatherRisks: WeatherPortRisk[],
) {
  const risk = analysis.risk_driver_breakdown;
  if (!risk) {
    return [];
  }

  const notes = risk.notes ?? {};
  const resin = analysis.resin_price_scenario;
  const marketRisk = analysis.market_price_risks[0];
  const news = analysis.top_news_events?.length ? analysis.top_news_events : latestNewsEvents;

  return [
    {
      key: "tariff_rate",
      label: "Tariff Rate",
      score: risk.tariff_rate,
      evidence: notes.tariff || "",
      effect: "A higher tariff score raises the duty shock applied to the material leg, so the P90 landed cost can move up even when supplier price is unchanged.",
      news: filterNews(news, ["tariff", "import", "policy", "duties"]),
    },
    {
      key: "freight_rate",
      label: "Freight Rate",
      score: risk.freight_rate,
      evidence: concreteJoin([notes.oil, notes.weather, notes.holidays], ""),
      effect: "This widens freight and delay paths in the Monte Carlo model, lifting the upper fan band when transport or port conditions worsen.",
      news: filterNews(news, ["freight", "shipping", "port", "congestion", "logistics"]),
    },
    {
      key: "fx_currency",
      label: "FX Currency",
      score: risk.fx_currency,
      evidence: concreteJoin([notes.macro_trade, notes.macro_ipi, notes.news], ""),
      effect: "This increases MYR conversion drift or volatility. A higher score makes unhedged imported quotes more exposed, while the hedge slider only narrows this FX part.",
      news: filterNews(news, ["ringgit", "myr", "usd", "currency", "forex", "oil"]),
    },
    {
      key: "oil_price",
      label: "Oil Price",
      score: risk.oil_price,
      evidence: notes.oil || "",
      effect: "Oil pressure feeds freight surcharge uncertainty. If Brent is rising, the fan chart widens through the logistics cost component.",
      news: filterNews(news, ["oil", "brent", "energy", "fuel"]),
    },
    {
      key: "weather_risk",
      label: "Weather Risk",
      score: risk.weather_risk,
      evidence: notes.weather || formatWeatherEvidence(latestWeatherRisks),
      effect: "Port weather risk increases delay probability and demurrage-style costs, so P90 rises through the delay and freight components.",
      news: filterNews(news, ["weather", "storm", "flood", "port"]),
    },
    {
      key: "holidays",
      label: "Holidays",
      score: risk.holidays,
      evidence: notes.holidays || "",
      effect: "Holiday closures raise lead-time risk during the 30-day window, so the model adds a delay-cost tail rather than changing the supplier base price.",
      news: filterNews(news, ["holiday", "closure", "festival"]),
    },
    {
      key: "macro_economy",
      label: "Macro Economy",
      score: risk.macro_economy,
      evidence: concreteJoin([notes.macro_trade, notes.macro_ipi], ""),
      effect: "OpenDOSM macro affects FX drift and inventory caution. A trade deficit weakens MYR risk; manufacturing contraction raises MOQ/dead-stock caution.",
      news: filterNews(news, ["manufacturing", "exports", "trade", "economy"]),
    },
    {
      key: "news_events",
      label: "News Events",
      score: risk.news_events,
      evidence: notes.news || formatNewsEvidence(news),
      effect: "Relevant GNews events increase FX, logistics, or tariff volatility depending on the article category and keywords selected for the run.",
      news: news.slice(0, 2),
    },
    {
      key: "pp_resin_benchmark",
      label: "PP Resin Benchmark",
      score: risk.pp_resin_benchmark,
      evidence: resin
        ? `${notes.resin || ""} SunSirs current PP benchmark is ${resin.current_price.toLocaleString()} ${formatResinUnit(resin.currency, resin.unit)} as of ${resin.as_of}.${marketRisk ? ` Selected quote is ${marketRisk.premium_pct.toFixed(1)}% vs benchmark and labelled ${marketRisk.risk_label.replaceAll("_", " ")}.` : ""}`
        : notes.resin || "",
      effect: "The SunSirs benchmark changes the resin requote factor and quote-vs-market warning. Wider PP benchmark range means more material-price tail risk.",
      news: filterNews(news, ["polypropylene", "pp resin", "petrochemical", "plastics", "polymer"]),
    },
  ].map((row) => ({
    ...row,
    hasConcreteEvidence: hasConcreteEvidence(row.evidence),
  })).sort((left, right) => right.score - left.score);
}

function filterNews(news: NewsEvent[], terms: string[]) {
  return news
    .filter((item) => terms.some((term) => `${item.title} ${item.notes}`.toLowerCase().includes(term)))
    .slice(0, 2);
}

function formatNewsEvidence(news: NewsEvent[]) {
  const top = news
    .slice()
    .sort((left, right) => (right.relevance_score ?? 0) - (left.relevance_score ?? 0))
    .slice(0, 3);
  if (!top.length) {
    return "No GNews snapshot is available for this run yet. Re-ingest news to show concrete article evidence.";
  }
  return `Top GNews signals: ${top
    .map((item) => `"${item.title || "Market event"}" from ${item.source || "unknown source"} (${Math.round((item.relevance_score ?? 0) * 100)}%)`)
    .join("; ")}.`;
}

function formatWeatherEvidence(risks: WeatherPortRisk[]) {
  const top = risks
    .slice()
    .sort((left, right) => (right.max_risk_score ?? 0) - (left.max_risk_score ?? 0))
    .slice(0, 3);
  if (!top.length) {
    return "No OpenWeather snapshot is available for this run yet. Re-ingest weather to show concrete port conditions.";
  }
  return `OpenWeather tracked procurement ports: ${top
    .map((risk) => {
      const port = risk.port_name || risk.port_code || "tracked port";
      const score = Math.round(risk.max_risk_score ?? 0);
      const summary = risk.raw_weather_summary || "weather risk";
      const slot = risk.worst_slot_date || "forecast window";
      return `${port} ${score}/100 on ${slot} (${summary})`;
    })
    .join("; ")}.`;
}

function formatResinUnit(currency: string, unit: string) {
  const normalizedUnit = unit.toUpperCase();
  if (normalizedUnit.includes(currency.toUpperCase())) {
    return normalizedUnit;
  }
  return `${currency}/${unit}`;
}

function concreteJoin(parts: Array<string | undefined>, fallback: string) {
  const concrete = parts.filter(Boolean);
  return concrete.length ? concrete.join(" ") : fallback;
}

function hasConcreteEvidence(evidence: string) {
  const text = evidence.trim().toLowerCase();
  if (!text) {
    return false;
  }
  return !(
    text.startsWith("no ") ||
    text.includes("not available") ||
    text.includes("neutral") ||
    text.includes("no high-relevance")
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
