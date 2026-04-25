"use client";

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { RankedQuote } from "@/lib/types";

import { CostBreakdown } from "./CostBreakdown";

interface SupplierCardProps {
  rankedQuote: RankedQuote;
  isRecommended: boolean;
  timingAdvice?: string;
  hedgeRec?: number;
  whyNotReason?: string;
  singleQuoteMode?: boolean;
  evaluationLabel?: string | null;
  savingsVsNextBest?: number;
}

const LABEL_COPY: Record<string, string> = {
  proceed: "Proceed",
  review_carefully: "Review Carefully",
  do_not_recommend: "Do Not Recommend",
};

const MARKET_RISK_COPY: Record<string, string> = {
  below_market: "Below market",
  fair: "Fair vs market",
  premium: "Premium",
  high_premium: "High premium",
};

const MARKET_RISK_CLASS: Record<string, string> = {
  below_market: "border-[#004aad]/40 text-[#004aad]",
  fair: "border-outline-variant text-on-background",
  premium: "border-[#b07d00] text-[#b07d00]",
  high_premium: "border-[#ba1a1a] bg-[#ba1a1a]/10 text-[#ba1a1a]",
};

export function SupplierCard({
  rankedQuote,
  isRecommended,
  timingAdvice,
  hedgeRec,
  whyNotReason,
  singleQuoteMode = false,
  evaluationLabel,
  savingsVsNextBest = 0,
}: SupplierCardProps) {
  const { quote, cost_result: cost, rank, delta_vs_winner } = rankedQuote;
  const marketRisk = rankedQuote.market_price_risk;
  
  const formatCurrency = (value: number) => `RM ${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

  if (isRecommended) {
    return (
      <div className="bg-white border-2 border-[#004aad] p-card-padding flex flex-col justify-between relative shadow-lg transform scale-[1.02] z-10 rounded-xl">
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#004aad] text-white text-[10px] font-black uppercase tracking-[0.2em] px-4 py-1.5 rounded-full shadow-md flex items-center gap-2 whitespace-nowrap">
          <span className="material-symbols-outlined text-[14px]">stars</span>
          {singleQuoteMode ? LABEL_COPY[evaluationLabel ?? "proceed"] ?? "Recommended" : "Recommended"}
        </div>
        <div>
          <div className="flex justify-between items-start mb-stack-md mt-stack-sm">
            <span className="text-label-caps text-[#004aad] uppercase font-bold tracking-widest">
              {!singleQuoteMode ? `Strategic Winner` : `Evaluation Result`}
            </span>
            <span className="material-symbols-outlined text-[#004aad]">check_circle</span>
          </div>
          <h2 className="text-display-lg font-display-lg mb-stack-xs text-[#004aad]">
            {quote.supplier_name ?? "Unknown supplier"}
          </h2>
          <p className="text-body-sm text-secondary mb-stack-lg font-medium">
            Lead time: {quote.lead_time_days ?? "-"} days
          </p>
          <div className="space-y-stack-md bg-slate-50 p-stack-md rounded-lg">
            {timingAdvice && (
              <div className="flex justify-between items-center py-stack-sm border-b border-slate-200">
                <span className="text-body-sm text-[#004aad] font-semibold">Timing</span>
                <span className="text-body-base font-bold text-on-background flex items-center gap-1">
                  {timingAdvice}
                </span>
              </div>
            )}
            {typeof hedgeRec === "number" && (
              <div className="flex justify-between items-center py-stack-sm border-b border-slate-200">
                <span className="text-body-sm text-secondary">Hedge %</span>
                <span className="text-data-mono font-data-mono font-bold text-[#004aad] text-lg">{hedgeRec}%</span>
              </div>
            )}
            <div className="flex justify-between items-center py-stack-sm border-b border-slate-200">
              <span className="text-body-sm text-secondary">Landed (p50)</span>
              <span className="text-h2 font-h2 text-[#004aad]">{formatCurrency(cost.total_landed_p50)}</span>
            </div>
            {!singleQuoteMode && (
              <div className="flex justify-between items-center py-stack-sm">
                <span className="text-body-sm text-secondary">Saved vs next-best</span>
                <span className="text-body-base font-bold text-[#00f5d4]">{formatCurrency(Math.max(savingsVsNextBest, 0))}</span>
              </div>
            )}
          </div>
        </div>

        {marketRisk && (
          <div className="mt-4 rounded-lg border border-outline-variant bg-surface-container-lowest p-3 text-xs text-secondary">
            <div className="mb-2 flex items-center justify-between gap-2">
              <span className="font-bold uppercase tracking-wider text-on-background">PP resin benchmark</span>
              <span className={`px-2 py-0.5 rounded border text-[10px] font-semibold uppercase ${MARKET_RISK_CLASS[marketRisk.risk_label]}`}>
                {MARKET_RISK_COPY[marketRisk.risk_label]}
              </span>
            </div>
            <div className="font-data-mono text-on-background">
              {marketRisk.premium_pct >= 0 ? "+" : ""}
              {marketRisk.premium_pct.toFixed(1)}% vs SunSirs CNY/MT benchmark
            </div>
          </div>
        )}

        <div className="mt-4">
          <CostBreakdown cost={cost} />
        </div>
      </div>
    );
  }

  // Not recommended card
  return (
    <div className="bg-white border border-outline-variant p-card-padding flex flex-col justify-between hover:border-slate-300 transition-all shadow-[0_2px_4px_rgba(0,0,0,0.02)] rounded-xl">
      <div>
        <div className="flex justify-between items-start mb-stack-md">
          <span className="text-label-caps text-secondary uppercase font-bold tracking-widest">Option 0{rank}</span>
          <span className="material-symbols-outlined text-slate-300">more_vert</span>
        </div>
        <h2 className="text-h2 font-h2 mb-stack-xs text-[#004aad]">
          {quote.supplier_name ?? "Unknown supplier"}
        </h2>
        <p className="text-body-sm text-secondary mb-stack-lg">
          Lead time: {quote.lead_time_days ?? "-"} days
        </p>
        <div className="space-y-stack-md">
          <div className="flex justify-between items-center py-stack-sm border-b border-slate-100">
            <span className="text-body-sm text-secondary">Landed (p50)</span>
            <span className="text-body-base font-semibold text-on-background">{formatCurrency(cost.total_landed_p50)}</span>
          </div>
          <div className="flex justify-between items-center py-stack-sm border-b border-slate-100">
            <span className="text-body-sm text-secondary">Vs Winner</span>
            <span className="font-data-mono font-bold text-[#ba1a1a]">+{formatCurrency(delta_vs_winner)}</span>
          </div>
        </div>
      </div>

      {marketRisk && (
        <div className="mt-4 rounded-lg border border-outline-variant bg-surface-container-lowest p-3 text-xs text-secondary">
          <div className="mb-2 flex items-center justify-between gap-2">
            <span className="font-bold uppercase tracking-wider text-on-background">PP resin benchmark</span>
            <span className={`px-2 py-0.5 rounded border text-[10px] font-semibold uppercase ${MARKET_RISK_CLASS[marketRisk.risk_label]}`}>
              {MARKET_RISK_COPY[marketRisk.risk_label]}
            </span>
          </div>
          <div className="font-data-mono text-on-background">
            {marketRisk.premium_pct >= 0 ? "+" : ""}
            {marketRisk.premium_pct.toFixed(1)}% vs SunSirs CNY/MT benchmark
          </div>
        </div>
      )}

      <div className="mt-4">
        <CostBreakdown cost={cost} />
      </div>

      {whyNotReason && (
        <Accordion className="mt-4 w-full">
          <AccordionItem value="why-not" className="border-b-0 border-outline-variant">
            <AccordionTrigger className="py-2 text-sm text-secondary hover:text-[#ba1a1a] hover:no-underline font-medium">
              Why not this supplier?
            </AccordionTrigger>
            <AccordionContent className="pt-2 text-sm leading-relaxed text-on-background">
              {whyNotReason}
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      )}
    </div>
  );
}
