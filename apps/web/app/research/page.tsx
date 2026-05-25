import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Research — benchmark, pre-registration, reproducibility",
  description:
    "Open-research page for TideGuard AI: PINN vs persistence and Lagrangian benchmarks, Diebold-Mariano test, pre-registration on OSF, carbon footprint and one-command reproduction.",
  alternates: { canonical: "/research" },
};

const GITHUB = "https://github.com/BitMagistrate/TideGuard";

export default function ResearchPage() {
  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="bg-gradient-to-br from-teal-700 to-ocean-600 text-white">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <p className="uppercase tracking-widest text-sand-100 text-xs mb-3">Open research</p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            Pre-registered. Reproducible. MIT-licensed.
          </h1>
          <p className="text-lg text-sand-50 mt-6 max-w-3xl">
            Every claim on this site is a number computed from the open code in this
            repository. The success rule was registered <em>before</em> we ran on real data.
            You can reproduce the headline benchmark on your laptop in ~10 minutes.
          </p>
          <div className="flex flex-wrap gap-2 mt-8 text-xs">
            <ResearchBadge>MIT License</ResearchBadge>
            <ResearchBadge>OSF pre-registered</ResearchBadge>
            <ResearchBadge>arXiv (in submission)</ResearchBadge>
            <ResearchBadge>Zenodo DOI</ResearchBadge>
            <ResearchBadge>CC-BY-4.0 curriculum</ResearchBadge>
            <ResearchBadge>OpenSSF Best Practices</ResearchBadge>
          </div>
        </div>
      </section>

      {/* Benchmark */}
      <section id="benchmark" className="max-w-5xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold">1. Benchmark</h2>
        <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">
          We benchmark the PINN against three published baselines on the synthetic
          Black-Sea test problem. Five independent training seeds. 14-day horizon.
          Headline number: <strong>RMSE 0.0929, NSE 0.913</strong>.
        </p>
        <div className="overflow-x-auto mt-6 rounded-2xl border border-zinc-200 dark:border-zinc-800">
          <table className="w-full text-sm">
            <thead className="bg-sand-50 dark:bg-zinc-900/60">
              <tr className="text-left">
                <th className="px-4 py-3">Model</th>
                <th className="px-4 py-3 text-right">RMSE ↓</th>
                <th className="px-4 py-3 text-right">NSE ↑</th>
                <th className="px-4 py-3 text-right">Δ vs persistence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
              <tr className="bg-teal-50/40 dark:bg-teal-950/30 font-semibold">
                <td className="px-4 py-3">PINN (ours)</td>
                <td className="px-4 py-3 text-right">0.0929</td>
                <td className="px-4 py-3 text-right">0.913</td>
                <td className="px-4 py-3 text-right text-teal-700">−7.6%</td>
              </tr>
              <tr>
                <td className="px-4 py-3">Lagrangian (5000 particles)</td>
                <td className="px-4 py-3 text-right">0.0972</td>
                <td className="px-4 py-3 text-right">0.904</td>
                <td className="px-4 py-3 text-right">−3.4%</td>
              </tr>
              <tr>
                <td className="px-4 py-3">Persistence</td>
                <td className="px-4 py-3 text-right">0.1006</td>
                <td className="px-4 py-3 text-right">0.898</td>
                <td className="px-4 py-3 text-right text-zinc-500">baseline</td>
              </tr>
              <tr>
                <td className="px-4 py-3">Climatology</td>
                <td className="px-4 py-3 text-right">0.1234</td>
                <td className="px-4 py-3 text-right">0.847</td>
                <td className="px-4 py-3 text-right text-zinc-500">+22.7%</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-sm text-zinc-500 mt-3">
          Diebold–Mariano test vs persistence: <code>p &lt; 3 × 10⁻¹¹²</code>.
          Bootstrap 95% CI on the RMSE difference is strictly negative — see the
          pre-registered acceptance rule below.
        </p>
      </section>

      {/* Pre-registration */}
      <section className="bg-sand-50 dark:bg-zinc-900/40 py-16">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold">2. Pre-registration acceptance rule</h2>
          <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">
            We pre-registered our success rule on OSF <em>before</em> running the model
            on real data. No selective reporting allowed.
          </p>
          <blockquote className="mt-6 border-l-4 border-teal-600 bg-white dark:bg-zinc-900 p-5 rounded-r-xl shadow-sm">
            <p className="text-zinc-700 dark:text-zinc-200">
              <em>“PINN beats baseline if and only if the Diebold–Mariano test
              yields <strong>p &lt; 0.05</strong> <strong>and</strong> the bootstrap 95%
              confidence interval on the RMSE-difference is strictly negative.
              If either fails, we report it and we ship the baseline.”</em>
            </p>
            <footer className="text-xs text-zinc-500 mt-3">
              OSF pre-registration, dated before the real-data run scheduled for
              summer 2026. Mirrored at <code>docs/pre_registration_osf.md</code>.
            </footer>
          </blockquote>
        </div>
      </section>

      {/* Theory of change */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold">3. Theory of change</h2>
        <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">
          The hypothesis we are actually testing: <strong>a public forecast 48–72 hours
          before plastic beaches enables volunteer crews to arrive in time and remove
          a measurable fraction of the macroplastic before it fragments</strong>.
        </p>
        <ol className="mt-6 space-y-3 list-decimal pl-6 text-zinc-700 dark:text-zinc-300">
          <li>Sentinel-2 + CMEMS currents + ERA5 wind → PINN forecast.</li>
          <li>Forecast → public map and B2G dashboard.</li>
          <li>Map → schools / NGOs / municipalities plan cleanups before the tide.</li>
          <li>Cleanups → measured kg removed, fed back into the next training cycle.</li>
          <li>Education module → next generation of citizen scientists.</li>
        </ol>
        <p className="text-sm text-zinc-500 mt-4">
          Full Mermaid diagram at <code>docs/theory_of_change.md</code>.
        </p>
      </section>

      {/* Reproducibility */}
      <section className="bg-sand-50 dark:bg-zinc-900/40 py-16">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold">4. Reproducibility</h2>
          <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">
            Reproduce the headline benchmark on your own laptop in ~10 minutes.
            No GPU required.
          </p>
          <pre className="mt-6 rounded-2xl bg-zinc-900 text-zinc-100 p-5 text-sm overflow-x-auto">{`git clone https://github.com/BitMagistrate/TideGuard
cd TideGuard/apps/ml
uv venv && uv pip install -e ".[dev]"
uv run python -m tideguard_ml.train --synthetic --epochs 5000
uv run python -m tideguard_ml.baselines.benchmark --seeds 5`}</pre>
          <p className="text-sm text-zinc-500 mt-3">
            Source: <a className="underline" href={`${GITHUB}/tree/main/apps/ml`}>apps/ml on GitHub</a>.
            Model card at <code>docs/model_card.md</code>.
          </p>
        </div>
      </section>

      {/* Carbon */}
      <section id="carbon" className="max-w-5xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold">5. Carbon footprint</h2>
        <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">
          We measure training emissions with{" "}
          <a className="underline" href="https://mlco2.github.io/codecarbon/">codecarbon</a>{" "}
          and inference at the per-call level. The numbers below are estimates for the
          central pilot scenario (500 kg of plastic intercepted in Anapa).
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <CarbonStat value="0.12 kg" label="CO₂e training (5-seed ensemble)" />
          <CarbonStat value="4 kg" label="CO₂e — one year of inference" />
          <CarbonStat value="1 150 kg" label="CO₂e prevented (500 kg plastic scenario)" />
          <CarbonStat value="≈ 279×" label="prevented per CO₂e spent" highlight />
        </div>
        <p className="text-sm text-zinc-500 mt-4">
          Methodology and references: <code>docs/IMPACT.md §2.3</code>.
        </p>
      </section>

      {/* Limitations */}
      <section className="bg-sand-50 dark:bg-zinc-900/40 py-16">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold">6. Honest limitations</h2>
          <ul className="mt-4 list-disc pl-6 space-y-2 text-zinc-700 dark:text-zinc-300">
            <li>Pilot data only — real-data validation is scheduled for <strong>summer 2026</strong>.</li>
            <li>Surface-only model (no vertical settling).</li>
            <li>River source term is approximated; rivers remain a major work item.</li>
            <li>Stokes drift not yet modelled — Open-Meteo Marine API is piped in but unused.</li>
            <li>Pre-revenue, founder + AI co-pilot, no signed B2G MoU. We say that on every page.</li>
          </ul>
          <p className="text-sm text-zinc-500 mt-6">
            Full FAQ for skeptical jurors: <Link href="/faq" className="underline">/faq</Link>.
          </p>
        </div>
      </section>
    </main>
  );
}

function ResearchBadge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-white/30 bg-white/10 px-3 py-1">
      {children}
    </span>
  );
}

function CarbonStat({ value, label, highlight }: { value: string; label: string; highlight?: boolean }) {
  return (
    <div
      className={`p-5 rounded-2xl border ${
        highlight
          ? "border-teal-600 bg-teal-50 dark:bg-teal-950/40"
          : "border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900"
      }`}
    >
      <div className={`text-2xl font-bold ${highlight ? "text-teal-700 dark:text-teal-300" : ""}`}>{value}</div>
      <div className="text-xs text-zinc-500 mt-2 leading-snug">{label}</div>
    </div>
  );
}
