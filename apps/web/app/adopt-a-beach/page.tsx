"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Segment = {
  id: string;
  slug: string;
  display_name: string;
  midpoint_lat: number;
  midpoint_lng: number;
  length_m: number;
  status: string;
};

export default function AdoptIndex() {
  const [segments, setSegments] = useState<Segment[]>([]);
  const [filter, setFilter] = useState("available");

  useEffect(() => {
    fetch(`${API}/adopt/segments?status=${filter}&limit=120`)
      .then(r => r.ok ? r.json() : [])
      .then(setSegments);
  }, [filter]);

  return (
    <main className="max-w-6xl mx-auto px-6 py-12">
      <h1 className="text-3xl font-bold">Adopt a beach</h1>
      <p className="text-zinc-500 text-sm mt-2 max-w-2xl">
        Take responsibility for a 1 km stretch of coastline. Get weekly forecasts, a public name on
        the map and a yearly impact certificate.
      </p>

      <div className="mt-6 flex gap-2 text-sm">
        {["available", "adopted", "all"].map(s => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-3 py-1 rounded-full border ${filter === s ? "bg-teal-600 text-white border-teal-600" : "bg-white"}`}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
        {segments.map(s => (
          <Link key={s.id} href={`/adopt-a-beach/segment/${s.slug}`}
                className="rounded-xl border p-5 hover:shadow-md">
            <div className="text-xs uppercase text-zinc-400">{s.slug}</div>
            <div className="font-semibold mt-1">{s.display_name}</div>
            <div className="text-xs text-zinc-500 mt-1">
              {s.midpoint_lat.toFixed(3)}°, {s.midpoint_lng.toFixed(3)}° · {Math.round(s.length_m)} m
            </div>
            <div className={`text-xs uppercase mt-2 ${s.status === "available" ? "text-teal-600" : "text-zinc-400"}`}>
              {s.status}
            </div>
          </Link>
        ))}
        {segments.length === 0 && <p className="text-zinc-400">No segments matching this filter.</p>}
      </div>
    </main>
  );
}
