import Link from "next/link";
import Image from "next/image";

const features = [
  {
    icon: "analytics",
    title: "Market Analysis",
    description: "Real-time pricing data for HS 3902.10 across Southeast Asian corridors.",
  },
  {
    icon: "security",
    title: "Risk Mitigation",
    description: "Automated compliance checks and supplier reliability scoring for Port Klang operations.",
  },
  {
    icon: "hub",
    title: "Hub Logistics",
    description: "Centralized command for freight forwarding and terminal handling at major trade ports.",
  },
];

const workflowSteps = ["Upload", "Review", "Analysis", "Decision"];

export default function Home() {
  return (
    <div className="font-body-base min-h-screen bg-[#eef0f4] text-on-surface antialiased">
      <header className="sticky top-0 z-50 flex h-12 w-full items-center justify-between border-b border-b-slate-200 bg-white px-7 font-['Inter'] tracking-tight shadow-[0_2px_4px_rgba(0,0,0,0.04)] antialiased">
        <div className="text-base font-black uppercase tracking-tighter text-[#004aad]">
          LintasNiaga
        </div>

        <nav className="hidden h-full items-center md:flex">
          {workflowSteps.map((step, index) => {
            const isActive = index === 0;

            return (
              <span
                key={step}
                className={`flex h-full cursor-pointer items-center gap-2 px-3 text-sm font-medium transition-colors duration-200 active:opacity-80 ${
                  isActive ? "text-[#004aad]" : "text-slate-500 hover:text-slate-800"
                }`}
              >
                <span
                  className={`flex h-5 w-5 items-center justify-center rounded-full border text-[11px] font-bold ${
                    isActive
                      ? "border-[#004aad] bg-[#004aad] text-white"
                      : "border-slate-300 bg-white text-slate-500"
                  }`}
                >
                  {index + 1}
                </span>
                <span>{step}</span>
                {index < workflowSteps.length - 1 ? (
                  <span className="ml-1 h-px w-8 bg-slate-300" aria-hidden="true" />
                ) : null}
              </span>
            );
          })}
        </nav>

        <div className="flex items-center gap-3">
          <button className="rounded-full p-1.5 text-slate-500 transition-colors hover:bg-slate-50">
            <span className="material-symbols-outlined text-[22px]">notifications</span>
          </button>
          <button className="rounded-full p-1.5 text-slate-500 transition-colors hover:bg-slate-50">
            <span className="material-symbols-outlined text-[22px]">help_outline</span>
          </button>
          <div className="flex h-7 w-7 items-center justify-center overflow-hidden rounded-full border border-slate-200 bg-slate-100 text-slate-700">
            <span className="material-symbols-outlined text-[20px]">person</span>
          </div>
        </div>
      </header>

      <main className="relative min-h-[calc(100vh-48px)] overflow-hidden">
        <section className="relative min-h-[calc(100vh-48px)] w-full px-6 pb-16 pt-20 sm:pt-24">
          <div className="pointer-events-none absolute inset-0 select-none overflow-hidden" aria-hidden="true">
            <Image
              alt=""
              src="/lintasniaga-landing-bg.png"
              fill
              priority
              sizes="100vw"
              className="object-cover object-center opacity-90"
            />
            <div className="absolute inset-0 bg-[#eef2f6]/50" />
            <div className="absolute inset-0 bg-[linear-gradient(to_bottom,rgba(238,242,246,0.72)_0%,rgba(238,242,246,0.35)_34%,rgba(238,242,246,0.58)_100%)]" />
          </div>

          <div className="relative z-10 mx-auto flex w-full max-w-6xl flex-col items-center">
            <div className="w-full max-w-5xl space-y-stack-lg text-center">
              <div className="flex justify-center">
                <span className="rounded-full border border-white/80 bg-[#d9eaff]/85 px-3 py-1 text-[11px] font-label-caps uppercase tracking-widest text-[#004aad] shadow-sm">
                  Procurement Intelligence
                </span>
              </div>

              <h1 className="mx-auto max-w-[920px] font-display-lg text-[34px] font-bold leading-[40px] text-primary sm:text-[38px] sm:leading-[44px] lg:text-[56px] lg:leading-[62px]">
                Choose the best-value supplier with less hidden risk
              </h1>

              <p className="mx-auto max-w-2xl font-body-base text-base font-medium leading-6 text-slate-700">
                Focus on PP Resin (HS 3902.10) for Port Klang hub. Streamline your global trade logistics with verified data synthesis and real-time risk assessment.
              </p>

              <div className="flex flex-col items-center justify-center gap-stack-md pt-1 sm:flex-row">
                <Link
                  href="/analysis/new"
                  className="group flex items-center gap-2 rounded-md bg-[#004aad] px-8 py-3 text-base font-semibold text-white shadow-lg shadow-[#004aad]/20 transition-all hover:brightness-110 active:scale-95 sm:px-10"
                >
                  Start Procurement Workflow
                  <span className="material-symbols-outlined transition-transform group-hover:translate-x-1">
                    arrow_forward
                  </span>
                </Link>
              </div>
            </div>

            <div className="mt-12 grid w-full grid-cols-1 gap-4 md:grid-cols-3">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="group flex flex-col gap-stack-sm rounded-md border border-slate-200/80 bg-white/[0.86] p-5 shadow-[0_4px_14px_rgba(15,23,42,0.08)] backdrop-blur-sm transition-colors hover:border-[#004aad]/50"
                >
                  <div className="flex h-9 w-9 items-center justify-center rounded-md bg-[#dbe8f8] text-[#004aad] transition-all group-hover:bg-[#004aad] group-hover:text-white">
                    <span className="material-symbols-outlined text-[21px]">{feature.icon}</span>
                  </div>
                  <h3 className="font-h2 text-base font-bold text-primary">{feature.title}</h3>
                  <p className="font-body-sm text-sm leading-6 text-secondary">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
