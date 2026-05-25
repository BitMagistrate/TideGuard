import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Roadmap 2026–2029",
  description:
    "Phased scale-out plan for TideGuard AI from a single Black-Sea pilot in 2026 to a global open forecast covering 30+ countries by 2029.",
  alternates: { canonical: "/roadmap" },
};

type Phase = {
  year: string;
  geography: string;
  reports: string;
  kg: string;
  countries: string;
  notes: string;
  highlight?: boolean;
};

const PHASES: Phase[] = [
  {
    year: "2026",
    geography: "Black Sea (RU coast)",
    reports: "5 000",
    kg: "1 200",
    countries: "1",
    notes: "Anchor pilot in Anapa + 3 schools, OSF preregistered real-data run.",
    highlight: true,
  },
  {
    year: "2027",
    geography: "+ BG / RO / TR coast",
    reports: "25 000",
    kg: "8 000",
    countries: "4",
    notes: "Cross-border MoUs, multilingual lessons (Bulgarian, Romanian, Turkish), first B2G dashboards signed.",
  },
  {
    year: "2028",
    geography: "+ Mediterranean + SE Asia",
    reports: "100 000",
    kg: "40 000",
    countries: "12",
    notes: "Stokes drift module + river-source coupling. Breakeven on B2G subscriptions.",
  },
  {
    year: "2029",
    geography: "Global",
    reports: "400 000",
    kg: "180 000",
    countries: "30+",
    notes: "Federated training across regional partners, multi-language Adopt-a-Beach.",
  },
];

export default function RoadmapPage() {
  return (
    <main className="min-h-screen">
      <section className="bg-gradient-to-br from-teal-700 to-ocean-600 text-white">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <p className="uppercase tracking-widest text-sand-100 text-xs mb-3">Roadmap</p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            From one beach in Anapa to 30+ countries in 4 years.
          </h1>
          <p className="text-lg text-sand-50 mt-6 max-w-3xl">
            We publish our scale-out plan in the open — including the failure points
            and the budgets. North-star metrics are written so any reader can hold
            us accountable next year.
          </p>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="overflow-x-auto rounded-2xl border border-zinc-200 dark:border-zinc-800">
          <table className="w-full text-sm">
            <thead className="bg-sand-50 dark:bg-zinc-900/60 text-left">
              <tr>
                <th className="px-4 py-3">Year</th>
                <th className="px-4 py-3">Geography</th>
                <th className="px-4 py-3 text-right">Citizen reports / yr</th>
                <th className="px-4 py-3 text-right">kg cleaned / yr</th>
                <th className="px-4 py-3 text-right">Countries</th>
                <th className="px-4 py-3">Milestone</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
              {PHASES.map((p) => (
                <tr
                  key={p.year}
                  className={
                    p.highlight ? "bg-teal-50/40 dark:bg-teal-950/30 font-semibold" : ""
                  }
                >
                  <td className="px-4 py-3 whitespace-nowrap">{p.year}</td>
                  <td className="px-4 py-3">{p.geography}</td>
                  <td className="px-4 py-3 text-right">{p.reports}</td>
                  <td className="px-4 py-3 text-right">{p.kg}</td>
                  <td className="px-4 py-3 text-right">{p.countries}</td>
                  <td className="px-4 py-3 text-zinc-600 dark:text-zinc-400 font-normal">
                    {p.notes}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="grid md:grid-cols-3 gap-4 mt-10">
          <Card label="Year 1 budget" value="$1 624" note="Hosting beyond free tier + 1 coastal trip" />
          <Card label="Year 2 run-rate" value="$3 000 / mo" note="Two co-leads, paid hosting, satellite quota" />
          <Card label="Year 4 run-rate" value="$8–12k / mo" note="Federated training cluster + regional engineers" />
        </div>
        <p className="text-sm text-zinc-500 mt-6">
          Detailed phase plan and unit economics: <code>docs/scaling_plan_2026_2029.md</code>.
          Risk register: <code>docs/risk_register.md</code>. North-star metrics are tracked
          publicly on the <Link href="/leaderboard" className="underline">leaderboard</Link>.
        </p>
      </section>

      <section className="bg-sand-50 dark:bg-zinc-900/40 py-14">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-2xl font-bold">Breakeven and sustainability</h2>
          <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">
            The public forecast and the lessons stay free by license. Premium API,
            B2G dashboards and Adopt-a-Beach fund the open platform. Year-1
            blended revenue is projected at €270k (B2G + grants); see{" "}
            <Link href="/pricing#economics" className="underline">/pricing</Link>.
            Breakeven on B2G subscriptions alone is projected for <strong>2028</strong>.
          </p>
        </div>
      </section>
    </main>
  );
}

function Card({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5">
      <div className="text-xs uppercase tracking-widest text-zinc-500">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
      <div className="text-sm text-zinc-500 mt-2">{note}</div>
    </div>
  );
}
