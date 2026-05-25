"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Region = { slug: string; display_name_en: string; country: string; beach_length_km: number };

export default function B2GIndex() {
  const [regions, setRegions] = useState<Region[]>([]);
  useEffect(() => {
    fetch(`${API}/b2g/dashboard/regions`)
      .then(r => r.ok ? r.json() : [])
      .then(setRegions);
  }, []);

  return (
    <main className="max-w-5xl mx-auto px-6 py-12">
      <h1 className="text-3xl font-bold">B2G dashboard — municipalities</h1>
      <p className="text-zinc-500 mt-2 text-sm max-w-2xl">
        Real-time pollution risk dashboard with VRP cleanup routing, alerts and a weekly auto-generated PDF.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
        {regions.map(r => (
          <Link key={r.slug} href={`/b2g/${r.slug}`} className="rounded-xl border p-5 hover:shadow-md">
            <div className="text-sm uppercase text-zinc-400">{r.country}</div>
            <div className="text-lg font-semibold mt-1">{r.display_name_en}</div>
            <div className="text-xs text-zinc-500 mt-1">≈ {r.beach_length_km} km beach</div>
          </Link>
        ))}
        {regions.length === 0 && <p className="text-zinc-400">No regions configured yet.</p>}
      </div>
    </main>
  );
}
