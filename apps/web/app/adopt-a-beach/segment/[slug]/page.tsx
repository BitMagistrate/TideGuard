"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const DEMO_MODE =
  (process.env.NEXT_PUBLIC_DEMO_MODE ?? "1") !== "0";

type Detail = {
  id: string;
  slug: string;
  display_name: string;
  midpoint_lat: number;
  midpoint_lng: number;
  length_m: number;
  status: string;
};

function authHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const tok = localStorage.getItem("tg.access_token");
  return tok ? { Authorization: `Bearer ${tok}` } : {};
}

export default function SegmentPage({ params }: { params: { slug: string } }) {
  const { slug } = params;
  const [d, setD] = useState<Detail | null>(null);
  const [tier, setTier] = useState("adopt_individual");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API}/adopt/segments/${slug}`).then(r => r.ok ? r.json() : null).then(setD);
  }, [slug]);

  async function adopt() {
    if (!d) return;
    if (DEMO_MODE) {
      setMsg(
        "Demo mode — Stripe checkout is disabled. In production this opens a hosted Stripe Checkout session. Set NEXT_PUBLIC_DEMO_MODE=0 to enable.",
      );
      return;
    }
    setBusy(true);
    try {
      const r = await fetch(`${API}/adopt/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeader() },
        body: JSON.stringify({ segment_id: d.id, tier, period: "monthly",
                                success_url: `${location.origin}/billing/success`,
                                cancel_url: `${location.origin}/billing/cancel` }),
      });
      const body = await r.json();
      if (body.checkout_url) location.href = body.checkout_url;
      else setMsg(body.detail || JSON.stringify(body));
    } finally { setBusy(false); }
  }

  if (!d) return <main className="max-w-3xl mx-auto px-6 py-12">Loading…</main>;
  return (
    <main className="max-w-3xl mx-auto px-6 py-12">
      <h1 className="text-3xl font-bold">{d.display_name}</h1>
      <p className="text-zinc-500 text-sm mt-1">
        Segment {d.slug} · midpoint {d.midpoint_lat.toFixed(4)}°, {d.midpoint_lng.toFixed(4)}° · length {Math.round(d.length_m)} m
      </p>
      <div className="mt-6 border rounded-xl p-5">
        <div className="text-xs uppercase text-zinc-400">Status</div>
        <div className="text-lg font-semibold capitalize">{d.status}</div>
        {d.status === "available" && (
          <div className="mt-4">
            <label className="text-sm">
              Choose plan:
              <select className="ml-2 border rounded px-2 py-1" value={tier} onChange={e => setTier(e.target.value)}>
                <option value="adopt_individual">Individual · $10/mo</option>
                <option value="adopt_school">School · $25/mo</option>
                <option value="adopt_business">Business · $200/mo</option>
              </select>
            </label>
            <div className="mt-3">
              <button onClick={adopt} disabled={busy}
                      className="bg-teal-600 text-white rounded-md px-4 py-2 hover:bg-teal-700 disabled:opacity-40">
                {busy ? "…" : "Adopt this beach"}
              </button>
            </div>
            {msg && (
              <p
                className={`text-sm mt-2 ${
                  msg.startsWith("Demo mode") ? "text-zinc-600" : "text-red-600"
                }`}
              >
                {msg}
              </p>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
