"use client";

import { ExternalLink } from "lucide-react";

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Skeleton } from "@/components/ui/skeleton";
import { RecommendationCard } from "@/lib/types";

interface ReasoningPanelProps {
  isLoading: boolean;
  recommendation?: RecommendationCard;
  traceUrl?: string | null;
}

export function ReasoningPanel({ isLoading, recommendation, traceUrl }: ReasoningPanelProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-6 w-3/4 bg-border" />
        <Skeleton className="h-20 w-full bg-border" />
        <Skeleton className="h-20 w-full bg-border" />
        <Skeleton className="h-20 w-full bg-border" />
      </div>
    );
  }

  if (!recommendation) {
    return null;
  }

  const backup = recommendation.backup_options[0];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-border pb-2">
        <h3 className="text-sm font-bold uppercase tracking-wider text-foreground">AI Analyst</h3>
        {traceUrl ? (
          <a
            href={traceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[11px] font-bold text-secondary-text transition-colors hover:text-primary"
          >
            View Langfuse Trace
            <ExternalLink size={12} />
          </a>
        ) : null}
      </div>

      <Accordion defaultValue={["reasoning"]} className="w-full">
        <AccordionItem value="reasoning" className="border-b-0">
          <AccordionTrigger className="py-2 text-sm font-semibold text-foreground hover:text-primary hover:no-underline">
            Why This Recommendation
          </AccordionTrigger>
          <AccordionContent className="space-y-4 pt-4">
            <div className="space-y-3">
              {recommendation.reasons.map((reason, index) => (
                <div
                  key={reason}
                  className="flex items-start gap-3 rounded-lg border border-border bg-[var(--color-surface-elevated)] p-3"
                >
                  <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--color-surface-strong)] text-[11px] font-bold text-foreground">
                    {index + 1}
                  </div>
                  <p className="text-sm leading-relaxed text-foreground">{reason}</p>
                </div>
              ))}
            </div>

            {recommendation.caveat ? (
              <div className="rounded-lg border-l-4 border-[var(--color-warning)] bg-[var(--color-surface-elevated)] p-3">
                <h4 className="mb-1 text-[11px] font-bold uppercase tracking-wider text-[var(--color-warning)]">
                  Risk Caveat
                </h4>
                <p className="text-sm text-foreground">{recommendation.caveat}</p>
              </div>
            ) : null}

            {backup ? (
              <div className="rounded-lg border border-border bg-[var(--color-surface-elevated)] p-3">
                <h4 className="mb-1 text-[11px] font-bold uppercase tracking-wider text-secondary-text">
                  Backup Option
                </h4>
                <p className="text-sm text-foreground">{backup.reason}</p>
                <p className="mt-2 text-xs text-secondary-text">Premium vs winner: RM {backup.premium_vs_winner.toLocaleString()}</p>
              </div>
            ) : null}

            {recommendation.impact_summary ? (
              <div className="rounded-lg border border-border bg-[var(--color-surface-elevated)] p-3">
                <h4 className="mb-1 text-[11px] font-bold uppercase tracking-wider text-secondary-text">
                  Impact Summary
                </h4>
                <p className="text-sm text-foreground">{recommendation.impact_summary}</p>
              </div>
            ) : null}
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}
