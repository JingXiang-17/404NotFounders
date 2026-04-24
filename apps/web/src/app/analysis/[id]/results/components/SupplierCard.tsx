"use client";

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  below_market: "border-primary/40 text-primary",
  fair: "border-border text-foreground",
  premium: "border-[var(--color-warning)] text-[var(--color-warning)]",
  high_premium: "border-[var(--color-warning)] bg-[var(--color-warning)]/10 text-[var(--color-warning)]",
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
  const cardClasses = isRecommended
    ? "border-2 border-primary bg-surface shadow-[0_0_20px_var(--color-success-glow)]"
    : "border border-border bg-[var(--color-surface-elevated)] opacity-90";

  const formatCurrency = (value: number) => `RM ${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

  return (
    <Card className={`overflow-hidden rounded-xl transition-all ${cardClasses}`}>
      <CardHeader className="p-4 pb-2">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="mb-1 flex items-center gap-2">
              {!singleQuoteMode ? <span className="text-sm font-bold text-secondary-text">#{rank}</span> : null}
              <CardTitle className="text-lg font-semibold text-foreground">{quote.supplier_name ?? "Unknown supplier"}</CardTitle>
            </div>
            <div className="text-sm text-secondary-text">Lead time: {quote.lead_time_days ?? "-"} days</div>
          </div>
          {isRecommended ? (
            <Badge className="bg-primary text-background hover:bg-primary">
              {singleQuoteMode ? LABEL_COPY[evaluationLabel ?? "proceed"] ?? "Recommended" : "Recommended"}
            </Badge>
          ) : null}
        </div>
      </CardHeader>

      <CardContent className="space-y-4 p-4 pt-2">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-secondary-text">Landed (p50)</div>
            <div className={`font-mono text-xl font-medium ${isRecommended ? "text-primary" : "text-foreground"}`}>
              {formatCurrency(cost.total_landed_p50)}
            </div>
          </div>
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-secondary-text">
              {isRecommended ? "Saved vs next-best" : "Vs Winner"}
            </div>
            <div className="font-mono text-lg text-foreground">
              {isRecommended ? formatCurrency(Math.max(savingsVsNextBest, 0)) : `+${formatCurrency(delta_vs_winner)}`}
            </div>
          </div>
        </div>

        {isRecommended ? (
          <div className="flex flex-wrap gap-2 border-t border-border pt-2">
            {timingAdvice ? <Badge variant="outline" className="border-border text-foreground">Timing: <span className="ml-1 text-primary">{timingAdvice}</span></Badge> : null}
            {typeof hedgeRec === "number" ? <Badge variant="outline" className="border-border text-foreground">Hedge: <span className="ml-1 text-primary">{hedgeRec}%</span></Badge> : null}
          </div>
        ) : null}

        {marketRisk ? (
          <div className="rounded-lg border border-border bg-background/30 p-3 text-xs text-secondary-text">
            <div className="mb-2 flex items-center justify-between gap-2">
              <span className="font-bold uppercase tracking-wider">PP resin benchmark</span>
              <Badge variant="outline" className={MARKET_RISK_CLASS[marketRisk.risk_label]}>
                {MARKET_RISK_COPY[marketRisk.risk_label]}
              </Badge>
            </div>
            <div className="font-mono text-foreground">
              {marketRisk.premium_pct >= 0 ? "+" : ""}
              {marketRisk.premium_pct.toFixed(1)}% vs SunSirs CNY/MT benchmark
            </div>
          </div>
        ) : null}

        <CostBreakdown cost={cost} />

        {!isRecommended && whyNotReason ? (
          <Accordion className="mt-2 w-full">
            <AccordionItem value="why-not" className="border-b-0 border-border">
              <AccordionTrigger className="py-2 text-sm text-secondary-text hover:text-[var(--color-warning)] hover:no-underline">
                Why not this supplier?
              </AccordionTrigger>
              <AccordionContent className="pt-2 text-sm leading-relaxed text-foreground">
                {whyNotReason}
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        ) : null}
      </CardContent>
    </Card>
  );
}
