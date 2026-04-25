import Link from "next/link";
import { cn } from "@/lib/utils";

type AnalysisStepId = "upload" | "review" | "analysis" | "decision";

interface AnalysisShellProps {
  currentStep: AnalysisStepId;
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
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
}: AnalysisShellProps) {
  const currentIndex = STEP_ORDER.indexOf(currentStep);

  return (
    <div className="min-h-screen bg-background font-body-base text-on-surface">
      {/* TopAppBar */}
      <header className="bg-white font-['Inter'] antialiased tracking-tight docked full-width top-0 border-b z-50 border-slate-200 shadow-[0_2px_4px_rgba(0,0,0,0.04)] fixed h-16 w-full px-6 flex justify-between items-center">
        <div className="flex items-center gap-12 h-full">
          <Link href="/" className="text-xl font-black text-[#004aad] tracking-tighter uppercase">
            LintasNiaga
          </Link>
          <nav className="hidden md:flex h-full items-center">
            {STEP_ORDER.map((step, index) => {
              const isCurrent = index === currentIndex;
              const isComplete = index < currentIndex;
              const isActive = isCurrent || isComplete;

              return (
                <div
                  key={step}
                  className={cn(
                    "h-full flex items-center gap-2 px-2 text-sm font-medium transition-colors duration-200 cursor-default",
                    isCurrent ? "text-[#004aad]" : "text-slate-500"
                  )}
                >
                  <span
                    className={cn(
                      "flex h-5 w-5 items-center justify-center rounded-full border text-[11px] font-bold",
                      isCurrent && "border-[#004aad] bg-[#004aad] text-white shadow-[0_0_0_3px_rgba(0,74,173,0.12)]",
                      isComplete && "border-[#004aad] bg-[#eaf2ff] text-[#004aad]",
                      !isActive && "border-slate-300 bg-white text-slate-400"
                    )}
                  >
                    {index + 1}
                  </span>
                  <span className={cn(isCurrent && "font-semibold")}>{STEP_LABELS[step]}</span>
                  {index < STEP_ORDER.length - 1 && (
                    <span
                      className={cn(
                        "mx-2 h-px w-8",
                        index < currentIndex ? "bg-[#004aad]" : "bg-slate-300"
                      )}
                      aria-hidden="true"
                    />
                  )}
                </div>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative hidden lg:block">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">search</span>
            <input className="pl-10 pr-4 py-1.5 bg-slate-50 border border-slate-200 rounded text-sm w-64 focus:ring-1 focus:ring-[#004aad] focus:border-[#004aad] outline-none" placeholder="Search procurement data..." type="text"/>
          </div>
          <div className="flex items-center gap-2">
            <button className="p-2 text-slate-500 hover:bg-slate-50 rounded cursor-pointer"><span className="material-symbols-outlined">notifications</span></button>
            <button className="p-2 text-slate-500 hover:bg-slate-50 rounded cursor-pointer"><span className="material-symbols-outlined">help_outline</span></button>
          </div>
          <img alt="User Profile" className="w-8 h-8 rounded-full border border-slate-200 object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDgkOHZJVmKieM3sDSa9mrj3RDO0oIsJotqH7ER53QMKsx6zWx_DaJTcMXznjuJfe5aSdlWOywxRVuTOSYZlemaClCn0tetQ_mY2rrnZ--T6ZVLuHRnfHa7wt5kl1SJRy1SvwiYWU4Ko9ZwjMyqusHvVyBGore3_D5H9ho3XnE3s987ArDL_zVGnCNSOp7QFo_v1oyF84OTq9nPCZSHKSi_OdsJ3pAXknbPwWD6Ml04pwUucfOHdXj0ualt379iF0qBt3e4Z6m-biY"/>
        </div>
      </header>

      {/* SideNavBar */}
      <aside className="bg-slate-50 text-sm font-medium font-['Inter'] fixed left-0 top-0 flex flex-col items-center py-8 z-40 docked h-screen w-20 border-r border-slate-200 pt-20">
        <div className="flex flex-col gap-2 w-full">
          <Link href="/" className="flex flex-col items-center justify-center text-slate-400 w-full py-4 hover:text-[#004aad] hover:bg-white transition-all cursor-pointer scale-95 active:scale-90">
            <span className="material-symbols-outlined">dashboard</span>
            <span className="text-[10px] mt-1">Dashboard</span>
          </Link>
          <div className="flex flex-col items-center justify-center bg-white text-[#004aad] border-r-4 border-[#004aad] w-full py-4 cursor-pointer scale-95 active:scale-90 transition-transform">
            <span className="material-symbols-outlined">analytics</span>
            <span className="text-[10px] mt-1">Insights</span>
          </div>
          <div className="flex flex-col items-center justify-center text-slate-400 w-full py-4 hover:text-[#004aad] hover:bg-white transition-all cursor-pointer scale-95 active:scale-90">
            <span className="material-symbols-outlined">inventory_2</span>
            <span className="text-[10px] mt-1">Archive</span>
          </div>
          <div className="flex flex-col items-center justify-center text-slate-400 w-full py-4 hover:text-[#004aad] hover:bg-white transition-all cursor-pointer scale-95 active:scale-90">
            <span className="material-symbols-outlined">settings</span>
            <span className="text-[10px] mt-1">Settings</span>
          </div>
        </div>
        <div className="mt-auto pb-4">
          <div className="w-10 h-10 bg-primary-container rounded flex items-center justify-center text-white">
            <span className="material-symbols-outlined">auto_awesome</span>
          </div>
        </div>
      </aside>

      {/* Main Content Canvas */}
      <main className="ml-20 pt-24 px-container-margin pb-12 min-h-screen">
        <div className="max-w-7xl mx-auto">
          {/* Page Header */}
          {(title || actions) && (
            <div className="flex justify-between items-end mb-stack-lg">
              <div>
                <nav className="flex gap-2 text-label-caps text-secondary mb-2 uppercase tracking-widest">
                  <span>Procurement</span>
                  <span>/</span>
                  <span className="text-[#004aad]">{STEP_LABELS[currentStep]}</span>
                </nav>
                <h1 className="font-h1 text-h1 text-on-background">{title}</h1>
                {subtitle && <p className="text-secondary mt-1 text-sm">{subtitle}</p>}
              </div>
              {actions && (
                <div className="flex gap-3">
                  {actions}
                </div>
              )}
            </div>
          )}

          {children}
        </div>
      </main>
    </div>
  );
}
