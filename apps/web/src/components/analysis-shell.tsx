import Link from "next/link";
import { Bell, CheckCircle2, Settings } from "lucide-react";

import { cn } from "@/lib/utils";

type AnalysisStepId = "upload" | "review" | "analysis" | "decision";

interface AnalysisShellProps {
  currentStep: AnalysisStepId;
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

const STEP_ORDER: AnalysisStepId[] = ["upload", "review", "analysis", "decision"];

const STEP_LABELS: Record<AnalysisStepId, string> = {
  upload: "Upload",
  review: "Review",
  analysis: "Analysis",
  decision: "Decision",
};

export function AnalysisShell({
  currentStep,
  title,
  subtitle,
  actions,
  children,
  footer,
}: AnalysisShellProps) {
  const currentIndex = STEP_ORDER.indexOf(currentStep);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-10">
        <header className="mb-8 flex flex-col gap-6 border-b border-border pb-5">
          <div className="flex items-start justify-between gap-4">
            <Link href="/" className="text-[2rem] font-semibold tracking-[-0.04em] text-foreground">
              LintasNiaga
            </Link>
            <div className="flex items-center gap-2 text-secondary-text">
              <span
                className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-border bg-surface text-secondary-text"
                aria-hidden="true"
              >
                <Bell size={18} />
              </span>
              <span
                className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-border bg-surface text-secondary-text"
                aria-hidden="true"
              >
                <Settings size={18} />
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-sm sm:gap-4">
            {STEP_ORDER.map((step, index) => {
              const isComplete = index < currentIndex;
              const isCurrent = index === currentIndex;

              return (
                <div key={step} className="flex items-center gap-3">
                  <div
                    className={cn(
                      "flex items-center gap-2 border-b-2 border-transparent pb-1 text-secondary-text",
                      isCurrent && "border-primary text-primary",
                      isComplete && "text-foreground",
                    )}
                  >
                    {isComplete ? (
                      <CheckCircle2 size={16} className="text-primary" />
                    ) : isCurrent ? (
                      <div className="h-2.5 w-2.5 rounded-full bg-primary shadow-[0_0_0_6px_rgba(13,255,214,0.10)]" />
                    ) : (
                      <div className="flex h-4 w-4 items-center justify-center rounded-full border border-secondary-text/50 text-[10px]">
                        {index + 1}
                      </div>
                    )}
                    <span className="font-medium">{STEP_LABELS[step]}</span>
                  </div>
                  {index < STEP_ORDER.length - 1 ? (
                    <div className="hidden h-px w-10 bg-border sm:block" />
                  ) : null}
                </div>
              );
            })}
          </div>

          {title || subtitle || actions ? (
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div className="space-y-2">
                {title ? <h1 className="text-3xl font-semibold tracking-[-0.03em] text-foreground">{title}</h1> : null}
                {subtitle ? <p className="max-w-3xl text-sm leading-6 text-secondary-text">{subtitle}</p> : null}
              </div>
              {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
            </div>
          ) : null}
        </header>

        <main className="flex-1">{children}</main>

        <footer className="mt-10 flex items-center justify-center border-t border-border pt-5 text-[11px] font-semibold uppercase tracking-[0.18em] text-secondary-text/70">
          {footer ?? "Powered by ilmu-glm-5.1 / Traces recorded in Langfuse"}
        </footer>
      </div>
    </div>
  );
}
