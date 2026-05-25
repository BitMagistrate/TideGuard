"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function EsgPage() {
  const [lat, setLat] = useState("43.5");
  const [lng, setLng] = useState("39.7");
  const [horizon, setHorizon] = useState("5");
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  async function compute() {
    setLoading(true);
    try {
      const r = await fetch(`${API}/esg/insurance/risk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lat: Number(lat), lng: Number(lng), horizon_years: Number(horizon) }),
      });
      setResult(r.ok ? await r.json() : { error: await r.text() });
    } finally { setLoading(false); }
  }

  return (
    <main className="max-w-3xl mx-auto px-6 py-12">
      <h1 className="text-3xl font-bold">ESG · Insurance risk</h1>
      <p className="text-zinc-500 text-sm mt-2 max-w-2xl">
        Deterministic 0–100 marine-plastic risk score with explainability. Used by insurers for
        coastal-property underwriting and by ESG reporters.{" "}
        <a href="/method" className="underline">methodology</a>.
      </p>
      <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-3">
        <input className="border rounded-md px-3 py-2" value={lat} onChange={e => setLat(e.target.value)} placeholder="lat" />
        <input className="border rounded-md px-3 py-2" value={lng} onChange={e => setLng(e.target.value)} placeholder="lng" />
        <input className="border rounded-md px-3 py-2" value={horizon} onChange={e => setHorizon(e.target.value)} placeholder="horizon years" />
        <button onClick={compute} disabled={loading}
                className="bg-teal-600 text-white rounded-md px-4 py-2 hover:bg-teal-700 disabled:opacity-40">
          {loading ? "computing…" : "compute"}
        </button>
      </div>
      {result && (
        <div className="mt-6 border rounded-xl p-5">
          <div className="text-3xl font-bold">{result.score} <span className="text-base text-zinc-500">/ 100</span></div>
          <div className="text-sm mt-1">Tier: <strong className="capitalize">{result.tier}</strong></div>
          <div className="text-xs text-zinc-500 mt-1">
            95 % CI: {result.confidence_95ci?.join("–")} · Methodology {result.methodology_version}
          </div>
          {result.components && (
            <div className="mt-4 text-sm">
              {Object.entries(result.components).map(([k, v]) => (
                <div key={k} className="flex justify-between border-b py-1">
                  <span className="capitalize">{k}</span><span>{String(v)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </main>
  );
}
