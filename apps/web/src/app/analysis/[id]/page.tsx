"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
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
        <section className="w-full bg-white border border-outline-variant p-card-padding rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
          <div className="flex items-center gap-4 border-b border-outline-variant pb-stack-md mb-stack-md">
            <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-surface-container-low border border-outline-variant">
              <span className="material-symbols-outlined text-[#004aad] text-3xl animate-pulse">analytics</span>
            </div>
            <div>
              <h1 className="font-h1 text-h1 text-on-background">Analyzing your quotes...</h1>
              <p className="mt-1 text-body-sm text-secondary">
                Step 3 is tied to the real backend run. Once the result endpoint resolves, this screen moves to the decision page automatically.
              </p>
            </div>
          </div>

          <div className="space-y-4 mb-stack-lg">
            {TIMELINE_STEPS.map((step, index) => {
              const isComplete = index < activeIndex || Boolean(resultQuery.data && index < TIMELINE_STEPS.length);
              const isActive = !resultQuery.data && index === activeIndex;

              return (
                <div
                  key={step.id}
                  className={[
                    "flex items-start gap-3 rounded p-4",
                    isActive ? "border-l-4 border-[#004aad] bg-surface-container-lowest" : "border-l-4 border-transparent",
                  ].join(" ")}
                >
                  <div className="mt-0.5">
                    {isComplete ? (
                      <span className="material-symbols-outlined text-[#004aad] text-xl">check_circle</span>
                    ) : isActive ? (
                      <span className="material-symbols-outlined text-[#004aad] text-xl animate-spin">refresh</span>
                    ) : (
                      <span className="material-symbols-outlined text-slate-300 text-xl">radio_button_unchecked</span>
                    )}
                  </div>
                  <div className={isActive ? "font-semibold text-on-background" : isComplete ? "text-on-background font-medium" : "text-secondary"}>
                    {step.label}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="bg-[#f7f9fb] border border-outline-variant rounded p-4 mb-stack-md">
            <p className="font-data-mono text-body-sm text-secondary whitespace-pre-wrap">{leadLine}</p>
          </div>

          {resultQuery.error && (
            <div className="mt-4 p-4 border border-[#ba1a1a] bg-[#fff9f9] rounded text-body-sm text-[#ba1a1a] flex flex-col gap-2">
              <div className="flex gap-2"><span className="material-symbols-outlined">error</span> {(resultQuery.error as Error).message}</div>
              <Link href="/analysis/new" className="font-bold underline uppercase text-[11px] tracking-widest mt-2">
                Return to upload
              </Link>
            </div>
          )}

          <div className="mt-6">
            <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-[#004aad] transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="mt-2 flex justify-between items-center text-[10px] font-bold tracking-widest text-secondary uppercase">
              <span>Estimated time: ~20 seconds</span>
              <span className="text-[#004aad]">{progress}%</span>
            </div>
          </div>
        </section>
      </div>
    </AnalysisShell>
  );
}
