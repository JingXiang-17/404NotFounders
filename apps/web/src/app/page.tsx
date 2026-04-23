import Link from "next/link";
import { ArrowRight, BarChart3, FileCheck2, ShieldAlert } from "lucide-react";

const featureCards = [
  {
    title: "Quote Intake",
    copy: "Upload up to five supplier PDFs and keep only valid or repaired quotes inside the comparison workflow.",
    icon: FileCheck2,
  },
  {
    title: "Deterministic Costing",
    copy: "Normalize FOB quotes into landed MYR cost using freight, tariff, and FX scenario inputs from the backend.",
    icon: BarChart3,
  },
  {
    title: "Bounded Reasoning",
    copy: "Use the recommendation layer for timing, hedge ratio, and caveats without disconnecting it from the math engine.",
    icon: ShieldAlert,
  },
];

const stepLabels = ["Upload", "Review", "Analysis", "Decision"];

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div className="text-[2rem] font-semibold tracking-[-0.04em] text-foreground">LintasNiaga</div>
          <Link
            href="/analysis/new"
            className="inline-flex h-11 items-center justify-center rounded-full bg-primary px-6 text-sm font-semibold text-background transition hover:opacity-90"
          >
            Start analysis
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 pb-14 pt-14">
        <section className="grid items-start gap-10 border-b border-border pb-14 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="space-y-8">
            <div className="space-y-5">
              <div className="inline-flex rounded-full border border-border bg-surface px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-secondary-text">
                Procurement decision copilot
              </div>
              <h1 className="max-w-4xl text-5xl font-semibold leading-[1.02] tracking-[-0.05em] md:text-7xl">
                Compare resin quotes without losing the actual decision path.
              </h1>
              <p className="max-w-2xl text-lg leading-8 text-secondary-text">
                Upload supplier PDFs, repair extracted fields, run deterministic landed-cost analysis, and move into a
                bounded recommendation page that stays tied to the backend result.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-4">
              <Link
                href="/analysis/new"
                className="inline-flex h-14 items-center gap-3 rounded-full bg-primary px-8 text-base font-semibold text-background transition hover:opacity-90"
              >
                Open workflow
                <ArrowRight size={18} />
              </Link>
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-secondary-text">
                PP Resin / FOB / Port Klang decision flow
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              {stepLabels.map((label, index) => (
                <div key={label} className="flex items-center gap-3">
                  <div className="rounded-full border border-border bg-surface px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-secondary-text">
                    {index + 1}. {label}
                  </div>
                  {index < stepLabels.length - 1 ? <div className="hidden h-px w-8 bg-border sm:block" /> : null}
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[28px] border border-border bg-surface p-4 shadow-[0_0_0_1px_rgba(13,255,214,0.10),0_0_40px_rgba(13,255,214,0.07)]">
            <div className="rounded-[24px] border border-border bg-[var(--color-surface-elevated)] p-6">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold uppercase tracking-[0.18em] text-secondary-text">Decision Console</div>
                  <div className="mt-2 text-2xl font-semibold text-foreground">Institutional workflow preview</div>
                </div>
                <div className="rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-primary">
                  Live flow
                </div>
              </div>

              <div className="space-y-4">
                <div className="rounded-2xl border border-border bg-background p-4">
                  <div className="text-[11px] font-bold uppercase tracking-[0.18em] text-secondary-text">Upload + review</div>
                  <div className="mt-3 text-lg font-semibold text-foreground">Keep only clean, scoped quotes</div>
                  <div className="mt-2 text-sm leading-6 text-secondary-text">
                    The frontend sends PDFs to `/quotes/upload`, then lets users repair extracted fields before ranking.
                  </div>
                </div>
                <div className="rounded-2xl border border-primary/30 bg-primary/10 p-4">
                  <div className="text-[11px] font-bold uppercase tracking-[0.18em] text-primary">Analysis</div>
                  <div className="mt-3 text-lg font-semibold text-foreground">Real run ID, real progress step</div>
                  <div className="mt-2 text-sm leading-6 text-foreground/80">
                    Step 3 now sits between review and decision, fetches <code>analysis/{"{run_id}"}</code>, and
                    redirects only after the backend result exists.
                  </div>
                </div>
                <div className="rounded-2xl border border-border bg-background p-4">
                  <div className="text-[11px] font-bold uppercase tracking-[0.18em] text-secondary-text">Decision</div>
                  <div className="mt-3 text-lg font-semibold text-foreground">FX, ranking, hedge, and reasons</div>
                  <div className="mt-2 text-sm leading-6 text-secondary-text">
                    The final page reads the stored result payload and keeps hedge simulation wired to the backend endpoint.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-6 pt-12 md:grid-cols-3">
          {featureCards.map((feature) => {
            const Icon = feature.icon;
            return (
              <div key={feature.title} className="rounded-2xl border border-border bg-surface p-8 transition hover:border-primary/35">
                <div className="mb-6 inline-flex rounded-2xl border border-border bg-background p-4">
                  <Icon className="h-6 w-6 text-primary" />
                </div>
                <h2 className="mb-3 text-2xl font-semibold tracking-[-0.03em] text-foreground">{feature.title}</h2>
                <p className="text-base leading-7 text-secondary-text">{feature.copy}</p>
              </div>
            );
          })}
        </section>
      </main>
    </div>
  );
}
