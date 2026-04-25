"use client";

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
        <Skeleton className="h-6 w-3/4 bg-slate-100" />
        <Skeleton className="h-20 w-full bg-slate-100" />
        <Skeleton className="h-20 w-full bg-slate-100" />
        <Skeleton className="h-20 w-full bg-slate-100" />
      </div>
    );
  }

  if (!recommendation) {
    return null;
  }

  const backup = recommendation.backup_options[0];

  return (
    <div className="space-y-4">
      {traceUrl && (
        <div className="flex justify-end">
          <a
            href={traceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[11px] font-bold tracking-widest uppercase text-[#004aad] transition-colors hover:opacity-80"
          >
            View Langfuse Trace
            <span className="material-symbols-outlined text-sm">open_in_new</span>
          </a>
        </div>
      )}

      <Accordion className="w-full">
        <AccordionItem value="reasoning" className="border-b-0">
          <AccordionTrigger className="py-2 text-sm font-semibold text-on-background hover:text-[#004aad] hover:no-underline">
            Why This Recommendation
          </AccordionTrigger>
          <AccordionContent className="space-y-4 pt-4">
            <div className="space-y-3">
              {recommendation.reasons.map((reason, index) => (
                <div
                  key={reason}
                  className="flex items-start gap-3 rounded-lg border border-outline-variant bg-surface-container-lowest p-3"
                >
                  <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#004aad]/10 text-[11px] font-bold text-[#004aad]">
                    {index + 1}
                  </div>
                  <p className="text-sm leading-relaxed text-on-background">{reason}</p>
                </div>
              ))}
            </div>

            {recommendation.caveat && (
              <div className="rounded-lg border-l-4 border-[#ffb400] bg-[#ffb400]/10 p-3">
                <h4 className="mb-1 text-[11px] font-bold uppercase tracking-wider text-[#b07d00] flex items-center gap-1">
                  <span className="material-symbols-outlined text-[14px]">warning</span> Risk Caveat
                </h4>
                <p className="text-sm text-on-background">{recommendation.caveat}</p>
              </div>
            )}

            {backup && (
              <div className="rounded-lg border border-outline-variant bg-surface-container-lowest p-3">
                <h4 className="mb-1 text-[11px] font-bold uppercase tracking-wider text-secondary">
                  Backup Option
                </h4>
                <p className="text-sm text-on-background">{backup.reason}</p>
                <p className="mt-2 text-xs font-medium text-secondary">Premium vs winner: RM {backup.premium_vs_winner.toLocaleString()}</p>
              </div>
            )}

            {recommendation.impact_summary && (
              <div className="rounded-lg border border-[#004aad]/30 bg-[#004aad]/5 p-3">
                <h4 className="mb-1 text-[11px] font-bold uppercase tracking-wider text-[#004aad]">
                  Impact Summary
                </h4>
                <p className="text-sm text-on-background">{recommendation.impact_summary}</p>
              </div>
            )}
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}
