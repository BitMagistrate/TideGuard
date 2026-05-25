import Link from "next/link";

const TIERS = [
  {
    slug: "free",
    name: "Free",
    price: "$0",
    period: "month",
    blurb: "Hobby & research access — fully attributed.",
    features: [
      "1 000 requests / month",
      "10 rps soft limit",
      "PINN forecast (7-day window)",
      "Citizen reports + cleanups",
      "Public widgets with attribution",
    ],
    cta: "Get a key",
    highlight: false,
  },
  {
    slug: "pro",
    name: "Pro",
    price: "$49",
    period: "month",
    blurb: "For startups, weather apps and small NGOs.",
    features: [
      "100 000 requests / month",
      "60 rps soft limit",
      "Historical archive: 30 days",
      "Forecast horizon: 14 days",
      "Removable attribution",
      "Email support",
    ],
    cta: "Start Pro",
    highlight: true,
  },
  {
    slug: "business",
    name: "Business",
    price: "$299",
    period: "month",
    blurb: "OGC WMS/WCS tiles, 1-year archive, 5 seats.",
    features: [
      "1 000 000 requests / month",
      "200 rps soft limit",
      "OGC WMS / WCS endpoints",
      "Historical archive: 365 days",
      "PDF & CSV exports",
      "Priority email support",
    ],
    cta: "Talk to sales",
    highlight: false,
  },
  {
    slug: "enterprise",
    name: "Enterprise",
    price: "Custom",
    period: "annual",
    blurb: "SLA-backed, dedicated VPC, custom regions.",
    features: [
      "Unlimited requests (fair-use)",
      "Custom SLA (99.9% / 99.95%)",
      "Private regions / on-prem",
      "Single-tenant deployment",
      "Dedicated support engineer",
    ],
    cta: "Contact us",
    highlight: false,
  },
];

const B2G_TIERS = [
  {
    slug: "b2g_basic",
    name: "B2G Basic",
    price: "$1 200",
    period: "month",
    features: ["1 region", "Weekly PDF report", "Email alerts", "Forecast dashboard"],
  },
  {
    slug: "b2g_pro",
    name: "B2G Pro",
    price: "$3 500",
    period: "month",
    features: ["3 regions", "VRP cleanup routing", "Telegram alerts", "API access", "GeoJSON export"],
  },
  {
    slug: "b2g_enterprise",
    name: "B2G Enterprise",
    price: "From $8 000",
    period: "month",
    features: ["Unlimited regions", "Multi-seat", "Custom integrations", "24×7 hotline", "On-site training"],
  },
];

const ADOPT_TIERS = [
  { slug: "adopt_individual", name: "Individual", price: "$10", period: "month", note: "Adopt 1 segment, public name on the map" },
  { slug: "adopt_school", name: "School", price: "$25", period: "month", note: "Adopt 5 segments, group dashboard" },
  { slug: "adopt_business", name: "Business", price: "$200", period: "month", note: "Adopt 10 segments, sponsor logo, CSR PDF" },
];

export default function PricingPage() {
  return (
    <main className="max-w-6xl mx-auto px-6 py-16">
      <header className="text-center mb-12">
        <h1 className="text-4xl font-bold">Pricing that scales with impact</h1>
        <p className="text-zinc-500 mt-2 max-w-2xl mx-auto">
          Soft-launch pricing. Every paid tier includes deterministic billing, webhook idempotency,
          and the right to delete your data in one click.
        </p>
      </header>

      <h2 className="text-xl font-semibold mb-4">Premium API tiers</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
        {TIERS.map(t => (
          <div
            key={t.slug}
            className={`rounded-2xl border p-6 ${t.highlight ? "border-teal-600 shadow-lg shadow-teal-100" : "border-zinc-200"}`}
          >
            <div className="text-xs uppercase tracking-widest text-zinc-400">{t.name}</div>
            <div className="text-3xl font-bold mt-2">{t.price}<span className="text-base text-zinc-500"> / {t.period}</span></div>
            <p className="text-sm text-zinc-500 mt-2">{t.blurb}</p>
            <ul className="text-sm mt-4 space-y-1">
              {t.features.map(f => <li key={f}>· {f}</li>)}
            </ul>
            <Link
              href={`/billing/checkout?tier=${t.slug}`}
              className={`block text-center mt-5 rounded-md px-4 py-2 text-sm font-medium ${t.highlight ? "bg-teal-600 text-white hover:bg-teal-700" : "bg-zinc-100 hover:bg-zinc-200"}`}
            >
              {t.cta}
            </Link>
          </div>
        ))}
      </div>

      <h2 className="text-xl font-semibold mb-4">B2G — municipalities & port authorities</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12">
        {B2G_TIERS.map(t => (
          <div key={t.slug} className="rounded-2xl border border-zinc-200 p-6">
            <div className="text-xs uppercase tracking-widest text-zinc-400">{t.name}</div>
            <div className="text-2xl font-bold mt-2">{t.price}<span className="text-sm text-zinc-500"> / {t.period}</span></div>
            <ul className="text-sm mt-4 space-y-1">
              {t.features.map(f => <li key={f}>· {f}</li>)}
            </ul>
          </div>
        ))}
      </div>

      <h2 className="text-xl font-semibold mb-4">Adopt-a-Beach</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {ADOPT_TIERS.map(t => (
          <div key={t.slug} className="rounded-2xl border border-zinc-200 p-6">
            <div className="text-xs uppercase tracking-widest text-zinc-400">{t.name}</div>
            <div className="text-2xl font-bold mt-2">{t.price}<span className="text-sm text-zinc-500"> / {t.period}</span></div>
            <p className="text-sm text-zinc-500 mt-2">{t.note}</p>
            <Link
              href="/adopt-a-beach"
              className="block text-center mt-5 rounded-md bg-teal-600 text-white px-4 py-2 text-sm font-medium hover:bg-teal-700"
            >
              Adopt a beach
            </Link>
          </div>
        ))}
      </div>

      {/* Economics at scale */}
      <section id="economics" className="mt-16 pt-14 border-t border-zinc-200 dark:border-zinc-800">
        <header className="text-center mb-8">
          <p className="uppercase tracking-widest text-xs text-teal-700 mb-2">Sustainability</p>
          <h2 className="text-3xl font-bold">Economics at scale</h2>
          <p className="text-sm text-zinc-500 mt-2 max-w-2xl mx-auto">
            Projected Year-1 unit economics. The public forecast and the 10-lesson
            curriculum stay free by license — the streams below fund them. Full
            assumptions are in <code>docs/MONETIZATION.md</code>.
          </p>
        </header>
        <div className="overflow-x-auto rounded-2xl border border-zinc-200 dark:border-zinc-800">
          <table className="w-full text-sm">
            <thead className="bg-sand-50 dark:bg-zinc-900/60 text-left">
              <tr>
                <th className="px-4 py-3">Stream</th>
                <th className="px-4 py-3">Pricing</th>
                <th className="px-4 py-3 text-right">Year-1 target</th>
                <th className="px-4 py-3 text-right">Projected revenue</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
              <tr><td className="px-4 py-3">B2G municipal</td><td className="px-4 py-3">€6 000 / city / yr</td><td className="px-4 py-3 text-right">4 cities</td><td className="px-4 py-3 text-right">€24 000</td></tr>
              <tr><td className="px-4 py-3">Corporate ESG report</td><td className="px-4 py-3">€18 000 / report</td><td className="px-4 py-3 text-right">6 reports</td><td className="px-4 py-3 text-right">€108 000</td></tr>
              <tr><td className="px-4 py-3">NGO data licence</td><td className="px-4 py-3">€1 200 / yr</td><td className="px-4 py-3 text-right">8 NGOs</td><td className="px-4 py-3 text-right">€9 600</td></tr>
              <tr><td className="px-4 py-3">Education licence</td><td className="px-4 py-3">€3 / pupil / yr</td><td className="px-4 py-3 text-right">1 200 pupils</td><td className="px-4 py-3 text-right">€3 600</td></tr>
              <tr><td className="px-4 py-3">Grants & sponsorship</td><td className="px-4 py-3">one-off</td><td className="px-4 py-3 text-right">—</td><td className="px-4 py-3 text-right">€120 000</td></tr>
              <tr className="bg-teal-50/40 dark:bg-teal-950/30 font-semibold">
                <td className="px-4 py-3">Total Year-1 (projected)</td>
                <td className="px-4 py-3"></td>
                <td className="px-4 py-3 text-right"></td>
                <td className="px-4 py-3 text-right text-teal-700">€265 200</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div className="grid md:grid-cols-3 gap-4 mt-8">
          <Stat label="Gross margin (B2G)" value="77%" note="Mostly software + thin services" />
          <Stat label="CAC payback" value="≈ 18 months" note="Mid-funnel B2G inquiry → signed pilot" />
          <Stat label="LTV / CAC" value="> 3×" note="Sustained renewal assumption, conservative" />
        </div>
        <p className="text-xs text-zinc-500 mt-6 text-center max-w-2xl mx-auto">
          These numbers are <strong>projections</strong>, not actuals. TideGuard is
          pre-revenue today. We label every public projection as such and refresh
          it each quarter in the open repository.
        </p>
      </section>

      <p className="mt-12 text-center text-xs text-zinc-500">
        Prices in USD · Annual plans save 17 % · VAT applied where required ·{" "}
        <Link href="/docs/billing" className="underline">Billing FAQ</Link>
      </p>
    </main>
  );
}

function Stat({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5">
      <div className="text-xs uppercase tracking-widest text-zinc-500">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
      <div className="text-sm text-zinc-500 mt-2">{note}</div>
    </div>
  );
}
