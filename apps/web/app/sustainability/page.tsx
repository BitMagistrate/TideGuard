"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

type Phase = { name: string; kwh: number; kg_co2e: number; method: string };
type Sustainability = {
  period_days: number;
  phases: Phase[];
  total_kwh: number;
  total_kg_co2e: number;
  comparison_short_haul_flight_kg: number;
  plastic_prevented_kg: number;
  net_kg_co2e_per_kg_plastic: number | null;
  notes: string[];
};

export default function SustainabilityPage() {
  const [data, setData] = useState<Sustainability | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/sustainability/footprint?period_days=30&plastic_prevented_kg=50`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`${r.status}`))))
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  if (error)
    return (
      <main className="mx-auto max-w-4xl p-8">
        <h1 className="text-3xl font-bold mb-4">Sustainability dashboard</h1>
        <p className="text-red-700">API unavailable: {error}</p>
      </main>
    );
  if (!data)
    return (
      <main className="mx-auto max-w-4xl p-8">
        <h1 className="text-3xl font-bold mb-4">Sustainability dashboard</h1>
        <p>Loading…</p>
      </main>
    );

  const flightShare = (data.total_kg_co2e / data.comparison_short_haul_flight_kg) * 100;

  return (
    <main className="mx-auto max-w-4xl p-8 space-y-8">
      <header>
        <h1 className="text-3xl font-bold mb-2">TideGuard sustainability ledger</h1>
        <p className="text-sm text-gray-600">
          Live carbon &amp; impact accounting for the last {data.period_days} days.
        </p>
      </header>

      <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card label="Energy used" value={`${data.total_kwh} kWh`} />
        <Card label="CO₂e emitted" value={`${data.total_kg_co2e} kg`} />
        <Card
          label="Plastic prevented"
          value={`${data.plastic_prevented_kg} kg`}
          subtle="from the latest cleanups stats"
        />
      </section>

      <section className="rounded-lg border border-gray-200 p-5">
        <h2 className="text-xl font-semibold mb-3">By phase</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500">
              <th>Phase</th>
              <th>Energy (kWh)</th>
              <th>CO₂e (kg)</th>
              <th>Method</th>
            </tr>
          </thead>
          <tbody>
            {data.phases.map((p) => (
              <tr key={p.name}>
                <td>{p.name}</td>
                <td>{p.kwh.toFixed(2)}</td>
                <td>{p.kg_co2e.toFixed(2)}</td>
                <td className="text-gray-500">{p.method}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="rounded-lg border border-gray-200 p-5 bg-green-50">
        <h2 className="text-xl font-semibold mb-2">Climate benchmark</h2>
        <p>
          A short-haul flight emits {data.comparison_short_haul_flight_kg} kg CO₂e
          per passenger. TideGuard&apos;s last {data.period_days}-day footprint is
          equivalent to <strong>{flightShare.toFixed(1)}&nbsp;%</strong> of one
          such flight.
        </p>
        {data.net_kg_co2e_per_kg_plastic !== null && (
          <p className="mt-2">
            Per kg of plastic prevented: <strong>{data.net_kg_co2e_per_kg_plastic}</strong>{" "}
            kg CO₂e — a strong net-positive when compared with the ~6 kg CO₂e
            embodied carbon of one kg of virgin PET.
          </p>
        )}
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-2">Notes</h2>
        <ul className="list-disc pl-6 text-sm text-gray-700">
          {data.notes.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}

function Card({
  label,
  value,
  subtle,
}: {
  label: string;
  value: string;
  subtle?: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
      {subtle && <p className="text-xs text-gray-400">{subtle}</p>}
    </div>
  );
}
