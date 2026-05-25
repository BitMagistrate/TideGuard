"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Summary = {
  org_id?: string;
  tier?: string;
  monthly_quota?: number;
  used_this_month?: number;
  remaining_this_month?: number;
  per_endpoint?: Record<string, number>;
};

function authHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const tok = localStorage.getItem("tg.access_token");
  return tok ? { Authorization: `Bearer ${tok}` } : {};
}

export default function UsagePage() {
  const [data, setData] = useState<Summary | null>(null);

  useEffect(() => {
    async function load() {
      const res = await fetch(`${API}/api_keys/usage/summary`, { headers: authHeader() });
      if (res.ok) setData(await res.json());
    }
    void load();
  }, []);

  if (!data) return <main className="max-w-3xl mx-auto px-6 py-12">Loading…</main>;
  const remaining = data.remaining_this_month ?? 0;
  const used = data.used_this_month ?? 0;
  const quota = data.monthly_quota ?? 1;
  const pct = Math.min(100, Math.round((used / quota) * 100));

  return (
    <main className="max-w-3xl mx-auto px-6 py-12">
      <h1 className="text-2xl font-bold">Usage</h1>
      <div className="mt-6 border rounded-xl p-5">
        <div className="text-sm text-zinc-500">Current tier</div>
        <div className="text-xl font-semibold mt-1">{data.tier ?? "free"}</div>

        <div className="text-sm text-zinc-500 mt-4">Used this month</div>
        <div className="text-3xl font-bold">{used.toLocaleString()} / {quota.toLocaleString()}</div>
        <div className="h-2 rounded-full bg-zinc-100 mt-2">
          <div className="h-2 rounded-full bg-teal-500" style={{ width: `${pct}%` }} />
        </div>
        <div className="text-xs text-zinc-500 mt-1">{remaining.toLocaleString()} requests remaining</div>
      </div>

      {data.per_endpoint && Object.keys(data.per_endpoint).length > 0 && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold">Per-endpoint breakdown</h2>
          <table className="w-full mt-4 text-sm">
            <tbody>
              {Object.entries(data.per_endpoint).map(([endpoint, count]) => (
                <tr key={endpoint} className="border-t">
                  <td className="py-2 font-mono text-xs">{endpoint}</td>
                  <td className="text-right">{count.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
