"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type ApiKey = {
  id: string;
  name: string;
  prefix: string;
  last4: string;
  status: string;
  scopes?: string[] | null;
  created_at?: string | null;
  last_used_at?: string | null;
};

function authHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const tok = localStorage.getItem("tg.access_token");
  return tok ? { Authorization: `Bearer ${tok}` } : {};
}

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [name, setName] = useState("primary");
  const [createdPlain, setCreatedPlain] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api_keys`, { headers: authHeader() });
      if (res.ok) setKeys(await res.json());
    } finally { setLoading(false); }
  }

  useEffect(() => { void refresh(); }, []);

  async function create() {
    const res = await fetch(`${API}/api_keys`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeader() },
      body: JSON.stringify({ name }),
    });
    if (res.ok) {
      const body = await res.json();
      setCreatedPlain(body.plaintext);
      void refresh();
    }
  }

  async function rotate(id: string) {
    const res = await fetch(`${API}/api_keys/${id}/rotate`, { method: "POST", headers: authHeader() });
    if (res.ok) {
      const body = await res.json();
      setCreatedPlain(body.plaintext);
      void refresh();
    }
  }

  async function revoke(id: string) {
    if (!confirm("Revoke this key? Applications using it will start failing immediately.")) return;
    await fetch(`${API}/api_keys/${id}`, { method: "DELETE", headers: authHeader() });
    void refresh();
  }

  return (
    <main className="max-w-4xl mx-auto px-6 py-12">
      <h1 className="text-2xl font-bold">API keys</h1>
      <p className="text-zinc-500 text-sm mt-1">
        Plaintext keys are shown only at creation/rotation time. Store them in your secrets manager immediately.
      </p>

      {createdPlain && (
        <div className="mt-4 border border-teal-500 bg-teal-50 rounded-md p-4">
          <div className="text-xs uppercase text-teal-700">New API key — copy it now</div>
          <code className="block font-mono text-sm mt-2 break-all">{createdPlain}</code>
          <button
            className="mt-2 text-xs underline"
            onClick={() => navigator.clipboard.writeText(createdPlain)}
          >
            Copy
          </button>
        </div>
      )}

      <div className="mt-6 flex gap-2">
        <input
          aria-label="API key name"
          className="border rounded-md px-3 py-2 flex-1"
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="key name"
        />
        <button
          onClick={create}
          className="bg-teal-600 text-white px-4 py-2 rounded-md hover:bg-teal-700"
        >
          Create key
        </button>
      </div>

      <table className="w-full mt-8 text-sm">
        <thead className="text-left text-xs uppercase text-zinc-500">
          <tr><th className="py-2">Name</th><th>Prefix</th><th>…last4</th><th>Status</th><th>Created</th><th /></tr>
        </thead>
        <tbody>
          {loading && <tr><td colSpan={6} className="py-4 text-zinc-400">loading…</td></tr>}
          {keys.map(k => (
            <tr key={k.id} className="border-t">
              <td className="py-3 font-medium">{k.name}</td>
              <td className="font-mono text-xs">{k.prefix}</td>
              <td className="font-mono text-xs">…{k.last4}</td>
              <td className={k.status === "active" ? "text-teal-600" : "text-zinc-400"}>{k.status}</td>
              <td className="text-xs text-zinc-500">{k.created_at?.slice(0, 10) ?? "—"}</td>
              <td>
                <button onClick={() => rotate(k.id)} className="text-xs underline mr-3">Rotate</button>
                <button onClick={() => revoke(k.id)} className="text-xs underline text-red-600">Revoke</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
