"use client";

import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { pdf } from "@react-pdf/renderer";
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
  const forecastEndDay = Math.max(0, (activeScenario?.p50_envelope?.length ?? 0) - 1);
  const forecastRangeLabel = forecastEndDay > 0 ? `D0 to D${forecastEndDay}` : "D0 to latest";
  const forecastTitle = forecastEndDay > 0 ? `${forecastEndDay}-Day Landed Cost Forecast` : "Landed Cost Forecast";
  const forecastSubtitle =
    forecastEndDay > 0
      ? `${forecastEndDay}-day landed-cost Monte Carlo across tariff, freight, FX, oil, weather, holidays, macro, news, and PP resin benchmark.`
      : "Landed-cost Monte Carlo across tariff, freight, FX, oil, weather, holidays, macro, news, and PP resin benchmark.";
  
  const latestNewsEvents = analysis?.top_news_events?.length
    ? analysis.top_news_events
    : latestNewsQuery.data?.data ?? [];
  const latestWeatherRisks = latestWeatherQuery.data?.data ?? [];

  return (
    <AnalysisShell
      currentStep="decision"
      title="Final Decision Recommendation"
      subtitle="Execution Strategy"
      actions={
        <div className="flex gap-stack-md">
          <button className="px-4 py-2 border border-outline-variant text-secondary font-body-base rounded-lg hover:bg-surface-container-low transition-colors flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px]">file_download</span>
            Export Report
          </button>
          <button className="px-6 py-2 bg-[#004aad] text-white font-body-base font-semibold rounded-lg shadow-sm hover:opacity-90 transition-opacity">
            Execute Procurement
          </button>
        </div>
      }
    >
      {analysisQuery.error ? (
        <div className="rounded-xl border border-[#ba1a1a] bg-[#fff9f9] p-4 text-sm text-[#ba1a1a] mb-stack-lg">
          {(analysisQuery.error as Error).message}
        </div>
      ) : null}

      <div className="mb-stack-lg grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard icon="currency_exchange" label={`Current FX (${pair ?? "N/A"})`} value={pair ? `${analysis?.fx_simulations[pair]?.current_spot?.toFixed(4) ?? "-"}` : "-"} helper="Spot used for locked hedge leg" />
        <KpiCard icon="local_shipping" label="Avg Landed Cost" value={formatMyr(avgCost)} helper="Supplier p50 average" />
        <KpiCard icon="gpp_maybe" label="P90 Risk Exposure" value={formatMyr(Math.max(0, p90Cost - expectedCost))} helper={`Fan width: ${formatMyr(riskWidth)}`} warning={Boolean(activeScenario?.p90_margin_wipeout_flag)} />
        <KpiCard icon="account_balance_wallet" label="Hedge Ratio" value={`${effectiveHedgeRatio}%`} helper={`Curve is ${direction}`} />
      </div>

      <div className="grid grid-cols-12 gap-gutter mb-stack-lg">
        {/* Main Chart Section */}
        <div className="col-span-12 xl:col-span-8 space-y-gutter">
          <div className="bg-white border border-outline-variant rounded-xl p-card-padding shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
            <div className="flex justify-between items-start mb-stack-md">
              <div>
                <h2 className="font-h2 text-h2 text-on-background">{forecastTitle}</h2>
                <p className="font-body-sm text-secondary mt-1">{forecastSubtitle}</p>
              </div>
              <div className="flex flex-col items-end gap-2">
                <div className="rounded-full border border-[#004aad]/30 bg-[#004aad]/10 px-3 py-1 text-xs font-semibold text-[#004aad]">
                  {forecastRangeLabel}
                </div>
                <div className="flex items-center gap-3 text-[10px] uppercase tracking-wider text-secondary">
                  <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-[#00f5d4]"></span> P10</span>
                  <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-[#004aad]"></span> P50</span>
                  <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-[#ff6b6b]"></span> P90</span>
                </div>
              </div>
            </div>

            {analysisQuery.isLoading ? <Skeleton className="h-[320px] w-full bg-slate-100" /> : null}
            {!analysisQuery.isLoading && activeScenario ? (
              <FxFanChart data={activeScenario} valuePrefix="RM " />
            ) : null}
            {!analysisQuery.isLoading && !activeScenario ? (
              <div className="rounded-lg border border-outline-variant bg-surface-container-lowest p-4 text-sm text-secondary">
                Landed-cost scenario is not available. Run analysis again after market snapshots are loaded.
              </div>
            ) : null}

            <div className="mt-4 grid gap-3 text-xs md:grid-cols-3">
              <div className="rounded-lg border border-outline-variant bg-surface-container-lowest p-3">
                <span className="block uppercase tracking-wider text-secondary">P10 optimistic</span>
                <span className="font-data-mono font-medium text-on-background text-sm">{formatMyr(activeScenario?.p10_envelope?.at(-1) ?? 0)}</span>
              </div>
              <div className="rounded-lg border border-[#004aad]/30 bg-[#004aad]/10 p-3">
                <span className="block uppercase tracking-wider text-[#004aad]">P50 expected</span>
                <span className="font-data-mono font-bold text-[#004aad] text-sm">{formatMyr(expectedCost)}</span>
              </div>
              <div className="rounded-lg border border-[#ba1a1a]/40 bg-[#ba1a1a]/10 p-3">
                <span className="block uppercase tracking-wider text-[#ba1a1a]">P90 stress</span>
                <span className="font-data-mono font-medium text-[#ba1a1a] text-sm">{formatMyr(p90Cost)}</span>
              </div>
            </div>

            <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(280px,420px)_minmax(0,1fr)]">
              {analysisQuery.isLoading ? (
                <Skeleton className="h-[132px] w-full bg-slate-100" />
              ) : (
                <HedgeSlider
                  hedgeRatio={effectiveHedgeRatio}
                  onHedgeChange={setHedgeRatio}
                  expectedLandedCost={expectedCost}
                />
              )}

              <div className="grid gap-3">
                <button
                  type="button"
                  onClick={() => bankDraftMutation.mutate(effectiveHedgeRatio)}
                  disabled={!analysis || bankDraftMutation.isPending}
                  className="flex min-h-[56px] w-full items-center justify-center gap-2 rounded-lg bg-[#004aad] px-4 py-3 text-sm font-bold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <span className="material-symbols-outlined text-[18px]">download</span>
                  {bankDraftMutation.isPending ? "Generating..." : "Generate Bank Instruction"}
                </button>
                <button
                  type="button"
                  disabled
                  title="V2 roadmap: direct API execution for API-first fintech partners."
                  className="flex min-h-[56px] w-full cursor-not-allowed items-center justify-center gap-2 rounded-lg border border-outline-variant bg-surface-container-low px-4 py-3 text-sm font-semibold text-secondary opacity-70"
                >
                  <span className="material-symbols-outlined text-[18px]">lock</span>
                  Execute via API (Coming Soon)
                </button>
                {pdfStatus ? <p className="text-xs text-[#004aad] font-medium">{pdfStatus}</p> : null}
              </div>
            </div>
          </div>
          
          <div className="bg-white border border-outline-variant p-card-padding rounded-xl shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
            <h2 className="text-label-caps font-label-caps text-secondary uppercase mb-stack-md flex items-center gap-2">
              <span className="material-symbols-outlined text-[#004aad] text-lg">smart_toy</span>
              Bounded AI Reasoning
            </h2>
            <ReasoningPanel
              isLoading={analysisQuery.isLoading}
              recommendation={analysis?.recommendation}
              traceUrl={analysis?.trace_url}
            />
          </div>
        </div>

        {/* Risk Panel Section */}
        <div className="col-span-12 xl:col-span-4">
          <RiskDriversPanel
            analysis={analysis}
            latestNewsEvents={latestNewsEvents}
            latestWeatherRisks={latestWeatherRisks}
          />
        </div>
      </div>

      <div className="bg-white border border-outline-variant p-card-padding rounded-xl shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-h2 font-h2 text-on-background">
            {analysis?.recommendation.mode === "single_quote" ? "Single Quote Evaluation" : "Active Procurement Quotes"}
          </h2>
          <div className="text-xs text-secondary">Quote-vs-PP-market badges are live from SunSirs snapshots.</div>
        </div>

        {analysisQuery.isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-[200px] w-full rounded-xl bg-slate-100" />
            <Skeleton className="h-[150px] w-full rounded-xl bg-slate-100" />
          </div>
        ) : null}

        <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
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
  const highlightedRows = rows.filter((row) => row.hasConcreteEvidence).slice(0, 4);

  return (
    <div className="h-full min-h-[720px] rounded-xl border border-outline-variant bg-white p-5 shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
      <div className="flex items-center justify-between gap-3 mb-stack-md">
        <h2 className="text-h2 font-h2 text-on-background flex items-center gap-2">
           <span className="material-symbols-outlined text-[#004aad]">security</span> Risk Drivers
        </h2>
        {highlightedRows.length ? (
          <span className="rounded-full bg-surface-container-high px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest text-on-surface">
            Top {highlightedRows.length}
          </span>
        ) : null}
      </div>

      {risk ? (
        <div className="max-h-[700px] space-y-3 overflow-y-auto pr-1">
          {highlightedRows.length ? highlightedRows.map((row) => (
            <div
              key={`insight-${row.key}`}
              className={`rounded-lg border bg-white p-3 ${riskSeverity(row.score).cardClass}`}
            >
              <div className="mb-2 flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-label-caps font-label-caps uppercase tracking-widest text-on-background">{row.label}</h3>
                  <p className="mt-1 text-[11px] leading-relaxed text-secondary">
                    {compactEvidence(row)} <span className="text-on-background font-medium">Impact:</span> {compactImpact(row)}
                  </p>
                </div>
                <span className={`shrink-0 rounded px-2 py-1 text-[9px] font-bold uppercase tracking-widest ${riskSeverity(row.score).badgeClass}`}>
                  {riskSeverity(row.score).label}
                </span>
              </div>
              {row.sourceLink ? (
                <a
                  href={row.sourceLink.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[11px] font-semibold text-[#004aad] transition hover:opacity-80"
                >
                  Source: {row.sourceLink.label}
                </a>
              ) : null}
            </div>
          )) : (
            <p className="rounded-lg border border-outline-variant bg-surface-container-lowest p-3 text-xs leading-relaxed text-secondary">
              No major live risk driver detected from current snapshots.
            </p>
          )}
        </div>
      ) : (
        <p className="mt-4 text-sm text-secondary">Risk driver analysis is not available yet.</p>
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
      impact: "possible duty shock and higher P90 landed cost",
    },
    {
      key: "freight_rate",
      label: "Freight Rate",
      score: risk.freight_rate,
      evidence: concreteJoin([notes.oil, notes.weather, notes.holidays], ""),
      effect: "This widens freight and delay paths in the Monte Carlo model, lifting the upper fan band when transport or port conditions worsen.",
      news: filterNews(news, ["freight", "shipping", "port", "congestion", "logistics"]),
      impact: "wider freight tail and delivery delay exposure",
    },
    {
      key: "fx_currency",
      label: "FX Currency",
      score: risk.fx_currency,
      evidence: concreteJoin([notes.macro_trade, notes.macro_ipi, notes.news], ""),
      effect: "This increases MYR conversion drift or volatility. A higher score makes unhedged imported quotes more exposed, while the hedge slider only narrows this FX part.",
      news: filterNews(news, ["ringgit", "myr", "usd", "currency", "forex", "oil"]),
      impact: "higher unhedged MYR conversion risk",
    },
    {
      key: "oil_price",
      label: "Oil Price",
      score: risk.oil_price,
      evidence: notes.oil || "",
      effect: "Oil pressure feeds freight surcharge uncertainty. If Brent is rising, the fan chart widens through the logistics cost component.",
      news: filterNews(news, ["oil", "brent", "energy", "fuel"]),
      impact: "freight surcharge pressure if Brent keeps rising",
    },
    {
      key: "weather_risk",
      label: "Weather Risk",
      score: risk.weather_risk,
      evidence: notes.weather || formatWeatherEvidence(latestWeatherRisks),
      effect: "Port weather risk increases delay probability and demurrage-style costs, so P90 rises through the delay and freight components.",
      news: filterNews(news, ["weather", "storm", "flood", "port"]),
      impact: "possible delay buffer and wider P90 freight tail",
    },
    {
      key: "holidays",
      label: "Holidays",
      score: risk.holidays,
      evidence: notes.holidays || "",
      effect: "Holiday closures raise lead-time risk during the forecast window, so the model adds a delay-cost tail rather than changing the supplier base price.",
      news: filterNews(news, ["holiday", "closure", "festival"]),
      impact: "lead-time buffer and delay-cost tail risk",
    },
    {
      key: "macro_economy",
      label: "Macro Economy",
      score: risk.macro_economy,
      evidence: concreteJoin([notes.macro_trade, notes.macro_ipi], ""),
      effect: "OpenDOSM macro affects FX drift and inventory caution. A trade deficit weakens MYR risk; manufacturing contraction raises MOQ/dead-stock caution.",
      news: filterNews(news, ["manufacturing", "exports", "trade", "economy"]),
      impact: "FX hedge caution and inventory/MOQ discipline",
    },
    {
      key: "news_events",
      label: "News Events",
      score: risk.news_events,
      evidence: notes.news || formatNewsEvidence(news),
      effect: "Relevant GNews events increase FX, logistics, or tariff volatility depending on the article category and keywords selected for the run.",
      news: news.slice(0, 2),
      impact: "market event risk across FX, logistics, or policy",
    },
    {
      key: "pp_resin_benchmark",
      label: "PP Resin Benchmark",
      score: risk.pp_resin_benchmark,
      evidence: resin
        ? `${notes.resin || ""} SunSirs current PP benchmark is ${resin.current_price.toLocaleString()} ${formatResinUnit(resin.currency, resin.unit)} as of ${resin.as_of}.${marketRisk ? ` Selected quote is ${marketRisk.premium_pct.toFixed(1)}% vs benchmark and labelled ${marketRisk.risk_label.replaceAll("_", " ")}.` : ""}`
        : notes.resin || "",
      effect: "The SunSirs benchmark flags quote-vs-market risk and helps catch premium, suspiciously low, or hidden-cost supplier pricing.",
      news: filterNews(news, ["polypropylene", "pp resin", "petrochemical", "plastics", "polymer"]),
      impact: "verify grade, validity, and hidden fees",
    },
  ].map((row) => ({
    ...row,
    hasConcreteEvidence: hasConcreteEvidence(row.evidence),
    sourceLink: firstNewsSource(row.news),
  })).sort((left, right) => right.score - left.score);
}

function riskSeverity(score: number) {
  if (score >= 0.75) {
    return {
      label: "High Risk",
      badgeClass: "bg-[#ba1a1a]/10 text-[#ba1a1a]",
      cardClass: "border-[#ba1a1a]/30",
    };
  }
  if (score >= 0.45) {
    return {
      label: "Medium Risk",
      badgeClass: "bg-[#ffb400]/15 text-[#b07d00]",
      cardClass: "border-[#ffb400]/30",
    };
  }
  return {
    label: "Watch",
    badgeClass: "bg-surface-container-high text-secondary",
    cardClass: "border-outline-variant",
  };
}

function compactEvidence(row: { evidence: string }) {
  return truncateSentence(row.evidence, 185);
}

function compactImpact(row: { impact: string; effect: string }) {
  return truncateSentence(row.impact || row.effect, 95);
}

function truncateSentence(value: string, maxLength: number) {
  const cleaned = value.replace(/\s+/g, " ").trim();
  if (cleaned.length <= maxLength) {
    return cleaned;
  }
  return `${cleaned.slice(0, maxLength - 1).trim()}...`;
}

function firstNewsSource(news: NewsEvent[]) {
  const first = news.find((item) => item.url);
  if (!first?.url) {
    return null;
  }
  return {
    url: first.url,
    label: first.source || "news",
  };
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
  icon: string;
  label: string;
  value: string;
  helper: string;
  warning?: boolean;
}) {
  return (
    <div className="rounded-xl border border-outline-variant bg-white p-4 shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
      <div className="mb-4 flex items-center justify-between text-secondary">
        <span className="text-[11px] font-bold uppercase tracking-[0.16em]">{label}</span>
        <span className={warning ? "text-[#ba1a1a] material-symbols-outlined text-[20px]" : "text-secondary material-symbols-outlined text-[20px]"}>{icon}</span>
      </div>
      <div className="font-data-mono text-2xl font-bold text-on-background">{value}</div>
      <div className={warning ? "mt-2 text-[11px] text-[#ba1a1a] font-medium" : "mt-2 text-[11px] text-[#004aad] font-medium"}>
        {helper}
      </div>
    </div>
  );
}
