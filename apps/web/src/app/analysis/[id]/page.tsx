"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { CheckCircle2, Loader2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { AnalysisShell } from "@/components/analysis-shell";
import { fetchApi } from "@/lib/api";
import { AnalysisResultPayload } from "@/lib/types";

interface TimelineStep {
  id: string;
  label: string;
}

const TIMELINE_STEPS: TimelineStep[] = [
  { id: "quotes", label: "Loaded valid quotes" },
  { id: "reference", label: "Loaded reference data (freight, tariffs)" },
  { id: "fx", label: "Fetched FX snapshots and built scenario envelopes" },
  { id: "landed-cost", label: "Computing landed cost per supplier" },
  { id: "ranking", label: "Ranking suppliers and fallback options" },
  { id: "reasoning", label: "Generating bounded AI reasoning" },
];

export default function AnalysisProgressPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const runId = params.id;
  const [visibleSteps, setVisibleSteps] = useState(2);
  const [analystLine, setAnalystLine] = useState("Preparing analyst trace...");

  const resultQuery = useQuery({
    queryKey: ["analysis-result", runId],
    enabled: Boolean(runId),
    queryFn: () => fetchApi<AnalysisResultPayload>(`/analysis/${runId}`),
    retry: 8,
    retryDelay: 500,
  });

  useEffect(() => {
    const handle = window.setInterval(() => {
      setVisibleSteps((current) => Math.min(current + 1, TIMELINE_STEPS.length - 1));
    }, 900);
    return () => window.clearInterval(handle);
  }, []);

  useEffect(() => {
    if (!runId) {
      return;
    }

    const source = new EventSource(`${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/analysis/${runId}/stream`);

    source.onmessage = (event) => {
      const nextText = event.data.replace(/\\n/g, "\n").trim();
      if (nextText) {
        setAnalystLine(nextText);
      }
    };

    source.onerror = () => {
      source.close();
    };

    return () => {
      source.close();
    };
  }, [runId]);

  useEffect(() => {
    if (!resultQuery.data) {
      return;
    }

    setVisibleSteps(TIMELINE_STEPS.length);
    const handle = window.setTimeout(() => {
      router.replace(`/analysis/${runId}/results`);
    }, 1200);

    return () => window.clearTimeout(handle);
  }, [resultQuery.data, router, runId]);

  const activeIndex = Math.min(visibleSteps - 1, TIMELINE_STEPS.length - 1);
  const completedCount = resultQuery.data ? TIMELINE_STEPS.length : Math.max(visibleSteps - 1, 0);
  const progress = Math.round((completedCount / TIMELINE_STEPS.length) * 100);

  const leadLine = useMemo(() => {
    if (resultQuery.data) {
      return "Analysis completed. Redirecting to decision workspace...";
    }
    return analystLine;
  }, [analystLine, resultQuery.data]);

  return (
    <AnalysisShell currentStep="analysis">
      <div className="mx-auto flex min-h-[65vh] w-full max-w-4xl items-center justify-center">
        <section className="w-full overflow-hidden rounded-2xl border border-border bg-surface">
          <div className="border-b border-border px-6 py-6">
            <div className="flex items-center gap-4">
              <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl border border-primary/20 bg-primary/10">
                <div className="absolute inset-0 rounded-2xl border border-primary/20 animate-pulse" />
                <div className="h-4 w-4 rounded-full bg-primary shadow-[0_0_18px_rgba(13,255,214,0.85)]" />
              </div>
              <div>
                <h1 className="text-4xl font-semibold tracking-[-0.04em] text-foreground">Analyzing your quotes...</h1>
                <p className="mt-2 text-sm text-secondary-text">
                  Step 3 is tied to the real backend run. Once the result endpoint resolves, this screen moves to the decision page automatically.
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-4 px-4 py-5 sm:px-6">
            {TIMELINE_STEPS.map((step, index) => {
              const isComplete = index < activeIndex || Boolean(resultQuery.data && index < TIMELINE_STEPS.length);
              const isActive = !resultQuery.data && index === activeIndex;

              return (
                <div
                  key={step.id}
                  className={[
                    "flex items-start gap-3 rounded-xl px-4 py-4",
                    isActive ? "border-l-2 border-primary bg-[var(--color-surface-elevated)]" : "",
                  ].join(" ")}
                >
                  <div className="mt-0.5">
                    {isComplete ? (
                      <CheckCircle2 size={18} className="text-primary" />
                    ) : isActive ? (
                      <Loader2 size={18} className="animate-spin text-primary" />
                    ) : (
                      <div className="mt-1 h-2.5 w-2.5 rounded-full bg-secondary-text/60" />
                    )}
                  </div>
                  <div className={isActive ? "font-medium text-foreground" : isComplete ? "text-foreground" : "text-secondary-text"}>
                    {step.label}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="px-6 pb-6">
            <div className="rounded-xl border border-border bg-background px-4 py-3 text-sm leading-6 text-secondary-text">
              {leadLine}
            </div>

            {resultQuery.error ? (
              <div className="mt-4 rounded-xl border border-[var(--color-warning)] bg-background px-4 py-3 text-sm text-[var(--color-warning)]">
                {(resultQuery.error as Error).message}
                <div className="mt-3">
                  <Link href="/analysis/new" className="font-semibold text-foreground underline decoration-primary/60 underline-offset-4">
                    Return to upload
                  </Link>
                </div>
              </div>
            ) : null}

            <div className="mt-6">
              <div className="h-2 overflow-hidden rounded-full bg-[var(--color-surface-strong)]">
                <div
                  className="h-full rounded-full bg-primary transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="mt-3 flex items-center justify-between text-[11px] font-semibold uppercase tracking-[0.18em] text-secondary-text">
                <span>Estimated time: ~20 seconds</span>
                <span className="text-primary">{progress}%</span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AnalysisShell>
  );
}
