"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function authHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const tok = localStorage.getItem("tg.access_token");
  return tok ? { Authorization: `Bearer ${tok}` } : {};
}

type Subscription = {
  tier_slug?: string;
  status?: string;
  current_period_start?: string;
  current_period_end?: string;
  cancel_at_period_end?: boolean;
  provider?: string;
};

export default function BillingPage() {
  const [sub, setSub] = useState<Subscription | null>(null);

  useEffect(() => {
    fetch(`${API}/billing/subscription`, { headers: authHeader() })
      .then(r => r.ok ? r.json() : null)
      .then(setSub);
  }, []);

  async function portal() {
    const r = await fetch(`${API}/billing/portal`, { method: "POST", headers: authHeader() });
    const body = await r.json();
    if (body.url) window.location.href = body.url;
  }
  async function cancel() {
    if (!confirm("Cancel at the end of the billing period?")) return;
    await fetch(`${API}/billing/cancel`, { method: "POST", headers: authHeader() });
    location.reload();
  }

  return (
    <main className="max-w-3xl mx-auto px-6 py-12">
      <h1 className="text-2xl font-bold">Billing</h1>
      {!sub && <p className="mt-4 text-zinc-500">You&apos;re on the free tier. Pick a plan on <a className="underline" href="/pricing">pricing</a>.</p>}
      {sub && (
        <div className="mt-6 border rounded-xl p-5">
          <div className="text-xs uppercase text-zinc-500">Current plan</div>
          <div className="text-2xl font-bold mt-1">{sub.tier_slug ?? "—"}</div>
          <div className="text-xs text-zinc-500 mt-1">Status: <span className="font-semibold">{sub.status}</span> · Provider: {sub.provider}</div>
          <div className="text-sm mt-3">
            Period: {sub.current_period_start?.slice(0, 10) ?? "—"} → {sub.current_period_end?.slice(0, 10) ?? "—"}
          </div>
          <div className="mt-5 flex gap-2">
            <button onClick={portal} className="px-4 py-2 rounded-md bg-zinc-100 hover:bg-zinc-200 text-sm">Manage payment method</button>
            {!sub.cancel_at_period_end && (
              <button onClick={cancel} className="px-4 py-2 rounded-md text-red-700 hover:bg-red-50 text-sm">Cancel at period end</button>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
