"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type ReportRow = {
  id: string;
  user_id: string;
  lat: number;
  lng: number;
  photo_url: string;
  severity: number;
  debris_type: string | null;
  status: string;
  created_at: string | null;
};

export default function ModeratorQueuePage() {
  const [token, setToken] = useState<string>("");
  const [rows, setRows] = useState<ReportRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setToken(localStorage.getItem("tideguard.admin_token") || "");
  }, []);

  const refresh = useCallback(async () => {
    setError(null);
    if (!token) {
      setRows(null);
      return;
    }
    setBusy(true);
    try {
      const res = await fetch(`${API}/reports/queue`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setRows(await res.json());
    } catch (exc) {
      setError(String(exc));
      setRows(null);
    } finally {
      setBusy(false);
    }
  }, [token]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const moderate = async (id: string, status: "approved" | "rejected") => {
    setBusy(true);
    try {
      const res = await fetch(`${API}/reports/${id}`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ status, moderator_note: status === "rejected" ? "Quality / safety issue" : null }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await refresh();
    } catch (exc) {
      setError(String(exc));
    } finally {
      setBusy(false);
    }
  };

  const saveToken = (next: string) => {
    setToken(next);
    localStorage.setItem("tideguard.admin_token", next);
  };

  return (
    <main className="min-h-screen max-w-5xl mx-auto px-6 py-10">
      <Link href="/admin" className="text-teal-700 text-sm">
        ← Back to KPI
      </Link>
      <h1 className="text-3xl font-bold mt-2 mb-2">Moderator queue</h1>
      <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-6">
        Reports stay in <code>pending</code> until a moderator approves them. Approved
        reports become visible on the public map.
      </p>

      <div className="flex gap-2 mb-4">
        <input
          type="password"
          value={token}
          onChange={(e) => saveToken(e.target.value)}
          placeholder="Paste your moderator JWT"
          aria-label="Moderator JWT"
          className="flex-1 px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-900"
        />
        <button
          onClick={() => void refresh()}
          disabled={busy}
          className="px-4 py-2 bg-teal-700 text-white rounded-lg disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      {error && <div className="mb-4 text-red-600 text-sm">{error}</div>}

      {!rows ? (
        <p className="text-zinc-500">Provide a moderator token to load the queue.</p>
      ) : rows.length === 0 ? (
        <p className="text-zinc-500">No pending reports. Nice work.</p>
      ) : (
        <div className="grid gap-4">
          {rows.map((r) => (
            <article
              key={r.id}
              className="flex gap-4 p-4 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900"
            >
              {r.photo_url ? (
                <img
                  src={r.photo_url.startsWith("http") ? r.photo_url : `${API}${r.photo_url}`}
                  alt={`Report ${r.id}`}
                  className="w-32 h-32 object-cover rounded-lg bg-zinc-100"
                />
              ) : (
                <div className="w-32 h-32 rounded-lg bg-zinc-100 flex items-center justify-center text-zinc-400 text-xs">
                  no image
                </div>
              )}
              <div className="flex-1">
                <div className="font-mono text-xs text-zinc-500">{r.id}</div>
                <div className="text-sm mt-1">
                  <strong>{r.debris_type ?? "unknown"}</strong> · severity {r.severity} · ({r.lat.toFixed(4)}, {r.lng.toFixed(4)})
                </div>
                <div className="text-xs text-zinc-500 mt-1">{r.created_at}</div>
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={() => void moderate(r.id, "approved")}
                    disabled={busy}
                    className="px-3 py-1 text-sm bg-teal-700 text-white rounded-lg disabled:opacity-50"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => void moderate(r.id, "rejected")}
                    disabled={busy}
                    className="px-3 py-1 text-sm border border-red-500 text-red-700 rounded-lg disabled:opacity-50"
                  >
                    Reject
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
