"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useState } from "react";

const ForecastMap = dynamic(() => import("@/components/Map/ForecastMap"), { ssr: false });

export default function MapPage() {
  const [day, setDay] = useState(0);
  const [mode, setMode] = useState<"concentration" | "exceedance">("concentration");
  const [quantile, setQuantile] = useState(0.9);

  return (
    <main className="min-h-screen flex flex-col">
      <header className="bg-teal-700 text-white px-6 py-4 flex justify-between items-center">
        <Link href="/" className="font-bold text-lg">TideGuard AI</Link>
        <nav className="flex gap-4 text-sm">
          <Link href="/map" className="opacity-90 hover:opacity-100">Map</Link>
          <Link href="/learn" className="opacity-90 hover:opacity-100">Learn</Link>
          <Link href="/leaderboard" className="opacity-90 hover:opacity-100">Leaderboard</Link>
        </nav>
      </header>

      <section className="flex-1 relative">
        <ForecastMap day={day} mode={mode} quantile={quantile} />

        <aside className="absolute top-4 right-4 bg-white dark:bg-zinc-900 rounded-xl shadow-lg p-4 w-72 z-10 space-y-4">
          <div>
            <h2 className="font-semibold mb-2">Layer</h2>
            <div className="flex rounded-lg overflow-hidden border border-zinc-200 dark:border-zinc-700 text-sm">
              <button
                type="button"
                onClick={() => setMode("concentration")}
                className={
                  "flex-1 py-1.5 " +
                  (mode === "concentration"
                    ? "bg-teal-600 text-white"
                    : "bg-white dark:bg-zinc-800 text-zinc-700 dark:text-zinc-200")
                }
              >
                Mean
              </button>
              <button
                type="button"
                onClick={() => setMode("exceedance")}
                className={
                  "flex-1 py-1.5 " +
                  (mode === "exceedance"
                    ? "bg-teal-600 text-white"
                    : "bg-white dark:bg-zinc-800 text-zinc-700 dark:text-zinc-200")
                }
              >
                P(exceed)
              </button>
            </div>
          </div>

          <div>
            <h2 className="font-semibold mb-2">Forecast horizon</h2>
            <input
              type="range"
              min={0}
              max={13}
              value={day}
              onChange={(e) => setDay(Number(e.target.value))}
              className="w-full accent-teal-600"
              aria-label="Forecast horizon in days"
            />
            <div className="text-sm text-zinc-600 dark:text-zinc-400 mt-1">D + {day}</div>
          </div>

          {mode === "exceedance" && (
            <div>
              <h2 className="font-semibold mb-2">Hotspot quantile</h2>
              <input
                type="range"
                min={0.5}
                max={0.99}
                step={0.01}
                value={quantile}
                onChange={(e) => setQuantile(Number(e.target.value))}
                className="w-full accent-teal-600"
                aria-label="Exceedance quantile"
              />
              <div className="text-sm text-zinc-600 dark:text-zinc-400 mt-1">
                top {(100 * (1 - quantile)).toFixed(0)}% (q={quantile.toFixed(2)})
              </div>
            </div>
          )}

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-2">
              {mode === "concentration" ? "Concentration" : "Probability of exceedance"}
            </h3>
            <div
              className={
                mode === "concentration"
                  ? "h-3 rounded-full bg-gradient-to-r from-ocean-500 via-yellow-400 to-red-500"
                  : "h-3 rounded-full bg-gradient-to-r from-zinc-200 via-amber-400 to-red-600"
              }
            />
            <div className="flex justify-between text-xs text-zinc-500 mt-1">
              <span>low</span>
              <span>high</span>
            </div>
          </div>

          <p className="text-[11px] text-zinc-500 leading-snug">
            P(exceed) shows the share of the 5-seed ensemble whose forecast for
            this cell exceeds the chosen quantile threshold. See{" "}
            <Link href="/method" className="underline hover:text-teal-600">
              /method
            </Link>{" "}
            for the calibration report.
          </p>
        </aside>
      </section>
    </main>
  );
}
