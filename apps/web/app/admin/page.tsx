import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const ADMIN_TOKEN = process.env.NEXT_PUBLIC_ADMIN_TOKEN || "";

type KPI = {
  users: number;
  reports_total: number;
  reports_approved: number;
  cleanups: number;
  kg_collected: number;
  schools: number;
  lessons_completed: number;
};

async function fetchKPI(): Promise<KPI | null> {
  // Try the protected /admin/kpi first (requires NEXT_PUBLIC_ADMIN_TOKEN);
  // gracefully fall back to the public KPI snapshot if no token is configured.
  try {
    if (ADMIN_TOKEN) {
      const res = await fetch(`${API}/admin/kpi`, {
        headers: { Authorization: `Bearer ${ADMIN_TOKEN}` },
        next: { revalidate: 30 },
      });
      if (res.ok) return await res.json();
    }
    const fallback = await fetch(`${API}/admin/kpi_public`, { next: { revalidate: 30 } });
    if (!fallback.ok) return null;
    return await fallback.json();
  } catch {
    return null;
  }
}

export default async function AdminPage() {
  const kpi = await fetchKPI();
  return (
    <main className="min-h-screen max-w-5xl mx-auto px-6 py-12">
      <Link href="/" className="text-teal-700 text-sm">
        ← Back home
      </Link>
      <div className="flex justify-between items-end mt-2 mb-6">
        <div>
          <h1 className="text-4xl font-bold">Impact KPI</h1>
          <p className="text-zinc-600 dark:text-zinc-400 mt-1">
            Read-only dashboard for jury &amp; partners. Authenticated counts when{" "}
            <code className="text-xs">NEXT_PUBLIC_ADMIN_TOKEN</code> is set;
            public snapshot otherwise.
          </p>
        </div>
        <Link
          href="/admin/queue"
          className="px-4 py-2 bg-teal-700 text-white rounded-lg text-sm hover:bg-teal-800"
        >
          Open moderator queue →
        </Link>
      </div>

      {!kpi ? (
        <p className="text-zinc-600">
          Could not load KPI — make sure the API is up and the public KPI
          endpoint (<code>/admin/kpi_public</code>) returns 200.
        </p>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard label="Users" value={kpi.users} />
          <KPICard
            label="Reports"
            value={kpi.reports_total}
            sub={`${kpi.reports_approved} approved`}
          />
          <KPICard label="Cleanups" value={kpi.cleanups} />
          <KPICard label="kg collected" value={kpi.kg_collected.toFixed(1)} />
          <KPICard label="Schools" value={kpi.schools} />
          <KPICard label="Lessons completed" value={kpi.lessons_completed} />
        </div>
      )}
    </main>
  );
}

function KPICard({ label, value, sub }: { label: string; value: number | string; sub?: string }) {
  return (
    <div className="p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
      <div className="text-3xl font-bold text-teal-700">{value}</div>
      <div className="text-sm text-zinc-500 mt-1">{label}</div>
      {sub && <div className="text-xs text-zinc-400 mt-1">{sub}</div>}
    </div>
  );
}
