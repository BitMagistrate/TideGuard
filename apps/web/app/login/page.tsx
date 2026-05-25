"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      const r = await fetch(`${API}/auth/magic_link`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, callback_url: `${location.origin}/auth/verify` }),
      });
      if (!r.ok) { setErr(await r.text()); return; }
      setSent(true);
    } finally { setBusy(false); }
  }

  return (
    <main className="max-w-md mx-auto px-6 py-16">
      <h1 className="text-3xl font-bold">Sign in</h1>
      <p className="text-zinc-500 text-sm mt-2">
        We&apos;ll email you a passwordless sign-in link. No tracking, no password to forget.
      </p>
      {!sent && (
        <form onSubmit={submit} className="mt-6 space-y-3">
          <input
            type="email" required value={email} onChange={e => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full border rounded-md px-3 py-2"
          />
          <button type="submit" disabled={busy}
                  className="w-full bg-teal-600 text-white rounded-md py-2 hover:bg-teal-700 disabled:opacity-40">
            {busy ? "Sending…" : "Send magic link"}
          </button>
          {err && <p className="text-sm text-red-600">{err}</p>}
        </form>
      )}
      {sent && (
        <div className="mt-6 p-4 border border-teal-500 bg-teal-50 rounded">
          Check your inbox for the sign-in link. It expires in 15 minutes.
        </div>
      )}
    </main>
  );
}
