import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const dynamic = "force-dynamic";
export const revalidate = 60;

type Impact = {
  region: string;
  window_days: number;
  n_reports: number;
  n_cleanups: number;
  volunteers: number;
  kg_total: number;
  co2_saved_kg: number;
  coastline_covered_km: number;
  methodology: {
    co2_per_kg: number;
    co2_source: string;
    coastline_norm_kg_per_km: number;
    coastline_source: string;
  };
};

async function fetchImpact(region?: string): Promise<Impact | null> {
  try {
    const url = region
      ? `${API}/b2g/impact?region=${encodeURIComponent(region)}&days=365`
      : `${API}/b2g/impact?days=365`;
    const res = await fetch(url, { next: { revalidate: 60 } });
    if (!res.ok) return null;
    return (await res.json()) as Impact;
  } catch {
    return null;
  }
}

function formatNumber(value: number): string {
  if (!Number.isFinite(value)) return "—";
  if (value >= 1000) return value.toLocaleString("en-US", { maximumFractionDigits: 0 });
  return value.toLocaleString("en-US", { maximumFractionDigits: 1 });
}

function StatCard({
  label,
  value,
  unit,
  hint,
}: {
  label: string;
  value: string;
  unit?: string;
  hint?: string;
}) {
  return (
    <div className="bg-white rounded-2xl shadow-sm p-6 border border-sand-100">
      <p className="text-sand-700 text-sm uppercase tracking-wider">{label}</p>
      <p className="text-4xl font-bold text-teal-700 mt-2">
        {value}
        {unit ? <span className="text-base text-sand-700 ml-1">{unit}</span> : null}
      </p>
      {hint ? <p className="text-xs text-sand-600 mt-2">{hint}</p> : null}
    </div>
  );
}

export default async function ImpactPage({
  searchParams,
}: {
  searchParams: Promise<{ region?: string }>;
}) {
  const params = await searchParams;
  const region = params?.region;
  const impact = await fetchImpact(region);

  return (
    <main className="min-h-screen bg-sand-50">
      <section className="bg-gradient-to-br from-teal-700 to-ocean-600 text-white">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <p className="uppercase tracking-widest text-sand-100 text-sm mb-3">
            TideGuard impact
          </p>
          <h1 className="text-4xl md:text-5xl font-bold mb-3">
            Trash removed. Coastline cleaner.
          </h1>
          <p className="text-lg text-sand-50 max-w-2xl">
            Verified citizen reports + community cleanups recorded over the past
            year. Methodology is documented inline so every number is auditable.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/impact"
              className={`px-4 py-2 rounded-full text-sm font-semibold ${
                !region ? "bg-white text-teal-700" : "bg-teal-800/40 hover:bg-teal-800/60"
              }`}
            >
              All regions
            </Link>
            {["anapa", "novorossiysk", "sochi", "azov"].map((r) => (
              <Link
                key={r}
                href={`/impact?region=${r}`}
                className={`px-4 py-2 rounded-full text-sm font-semibold capitalize ${
                  region === r ? "bg-white text-teal-700" : "bg-teal-800/40 hover:bg-teal-800/60"
                }`}
              >
                {r}
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-12">
        {impact ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <StatCard
                label="Citizen reports"
                value={formatNumber(impact.n_reports)}
                hint={`In the last ${impact.window_days} days`}
              />
              <StatCard
                label="Cleanup events"
                value={formatNumber(impact.n_cleanups)}
                hint={`${formatNumber(impact.volunteers)} volunteers`}
              />
              <StatCard
                label="Plastic collected"
                value={formatNumber(impact.kg_total)}
                unit="kg"
              />
              <StatCard
                label="CO\u2082 avoided"
                value={formatNumber(impact.co2_saved_kg)}
                unit="kg CO\u2082e"
                hint={impact.methodology.co2_source}
              />
              <StatCard
                label="Coastline covered"
                value={formatNumber(impact.coastline_covered_km)}
                unit="km"
                hint={impact.methodology.coastline_source}
              />
              <StatCard
                label="Region"
                value={impact.region}
                hint={`window = ${impact.window_days} d`}
              />
            </div>

            <section className="mt-12 bg-white rounded-2xl shadow-sm p-8 border border-sand-100">
              <h2 className="text-2xl font-bold text-teal-800 mb-3">Methodology</h2>
              <ul className="text-sand-800 space-y-2">
                <li>
                  <strong>CO\u2082 avoided</strong>: <code>kg_total \u00d7 {impact.methodology.co2_per_kg}</code> kg CO\u2082e
                  per kg \u2014 source: {impact.methodology.co2_source}.
                </li>
                <li>
                  <strong>Coastline covered</strong>:{" "}
                  <code>\u221a(kg_total / {impact.methodology.coastline_norm_kg_per_km})</code> km \u2014
                  source: {impact.methodology.coastline_source}.
                </li>
                <li>
                  <strong>Counts</strong> come from the live operational database
                  (citizen reports + verified cleanups).
                </li>
              </ul>
              <p className="text-sm text-sand-600 mt-6">
                Raw aggregates are also exposed by the API at{" "}
                <code className="bg-sand-100 px-1.5 py-0.5 rounded">GET /b2g/impact</code>.
              </p>
            </section>
          </>
        ) : (
          <div className="bg-white rounded-2xl border border-sand-100 p-12 text-center text-sand-700">
            <p className="text-lg">Impact data is not yet available.</p>
            <p className="text-sm mt-2">
              Make sure the API is running at{" "}
              <code className="bg-sand-100 px-1.5 py-0.5 rounded">{API}</code>.
            </p>
          </div>
        )}
      </section>
    </main>
  );
}
