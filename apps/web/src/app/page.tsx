import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-background px-4 sm:px-6 lg:px-8 py-12">
      <main className="flex-1 w-full max-w-5xl flex flex-col items-center justify-center space-y-12 text-center mt-12">
        <div className="space-y-6 max-w-3xl">
          <h1 className="text-[48px] font-bold text-foreground leading-tight tracking-tight">
            Choose the best-value supplier with less hidden risk
          </h1>
          <p className="text-lg md:text-xl text-secondary-text max-w-2xl mx-auto leading-relaxed">
            LintasNiaga compares FOB PP Resin quotes, simulates FX scenarios, and recommends the best-value supplier for Malaysian importers.
          </p>
        </div>

        <div>
          <Link
            href="/analysis/new"
            className="inline-flex h-12 items-center justify-center rounded-[8px] bg-primary px-8 text-sm font-semibold text-[#06060A] hover:bg-[#00e0bb] transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background"
          >
            Start Analysis
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mt-16 pt-8">
          {[
            { title: "Multi-Supplier Comparison", desc: "Instantly compare multiple quotes from suppliers." },
            { title: "FX Risk Simulation", desc: "Simulate exchange rate movements for true cost." },
            { title: "Explainable AI Reasoning", desc: "Get detailed, transparent breakdown of recommendations." },
          ].map((feature, idx) => (
            <div key={idx} className="bg-surface border border-border rounded-[12px] p-8 text-left hover:border-primary/30 transition-colors">
              <h3 className="text-lg font-semibold text-foreground mb-3">{feature.title}</h3>
              <p className="text-sm text-secondary-text leading-relaxed">
                {feature.desc}
              </p>
            </div>
          ))}
        </div>
      </main>

      <footer className="w-full max-w-5xl mt-auto pt-12 pb-6 border-t border-border mt-24 text-center">
        <p className="text-sm text-secondary-text">
          UMHackathon 2026 · Domain 2 · Built on Z.AI GLM-5.1
        </p>
      </footer>
    </div>
  );
}
