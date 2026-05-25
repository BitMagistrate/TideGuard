"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function WidgetInstallPage() {
  const [lat, setLat] = useState("43.5");
  const [lng, setLng] = useState("39.7");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [horizon, setHorizon] = useState("3");
  const widgetUrl = `${API}/widgets/beach_status?lat=${lat}&lng=${lng}&theme=${theme}&horizon=${horizon}`;
  const jsonUrl = `${API}/widgets/beach_status.json?lat=${lat}&lng=${lng}&horizon=${horizon}`;
  const qrUrl = `${API}/widgets/beach_status/qr?lat=${lat}&lng=${lng}`;
  const iframe = `<iframe src="${widgetUrl}" width="320" height="180" style="border:0" loading="lazy"></iframe>`;

  return (
    <main className="max-w-3xl mx-auto px-6 py-12">
      <h1 className="text-3xl font-bold">Embed widget</h1>
      <p className="text-zinc-500 text-sm mt-1">
        Drop the beach-status widget onto your site or print the QR for a beach noticeboard.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
        <label className="text-sm">lat <input value={lat} onChange={e => setLat(e.target.value)} className="w-full border rounded px-2 py-1" /></label>
        <label className="text-sm">lng <input value={lng} onChange={e => setLng(e.target.value)} className="w-full border rounded px-2 py-1" /></label>
        <label className="text-sm">horizon (days) <input value={horizon} onChange={e => setHorizon(e.target.value)} className="w-full border rounded px-2 py-1" /></label>
        <label className="text-sm">theme
          <select value={theme} onChange={e => setTheme(e.target.value as "light" | "dark")} className="w-full border rounded px-2 py-1">
            <option value="light">light</option><option value="dark">dark</option>
          </select>
        </label>
      </div>

      <h2 className="text-lg font-semibold mt-8">Preview</h2>
      <iframe src={widgetUrl} className="border rounded-md mt-2" width={320} height={180} />

      <h2 className="text-lg font-semibold mt-8">Embed code</h2>
      <textarea value={iframe} readOnly className="w-full border rounded p-3 font-mono text-xs h-24" />

      <h2 className="text-lg font-semibold mt-8">QR code for noticeboards</h2>
      <img src={qrUrl} alt="QR" className="mt-2 border rounded" />

      <h2 className="text-lg font-semibold mt-8">JSON endpoint (public, attribution required)</h2>
      <code className="block bg-zinc-50 p-3 rounded text-xs">{jsonUrl}</code>
      <p className="text-xs text-zinc-500 mt-2">By embedding the widget you agree to keep the &ldquo;Powered by TideGuard&rdquo; attribution visible.</p>
    </main>
  );
}
