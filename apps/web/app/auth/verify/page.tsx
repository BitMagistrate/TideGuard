"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function VerifyPage() {
  const [status, setStatus] = useState<"loading" | "ok" | "fail">("loading");
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const token = params.get("token");
    if (!token) { setStatus("fail"); setMsg("Missing token."); return; }
    (async () => {
      const r = await fetch(`${API}/auth/verify`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });
      if (!r.ok) { setStatus("fail"); setMsg(await r.text()); return; }
      const body = await r.json();
      localStorage.setItem("tg.access_token", body.access_token);
      setStatus("ok");
      setTimeout(() => { location.href = "/dashboard"; }, 700);
    })();
  }, []);

  return (
    <main className="max-w-md mx-auto px-6 py-16 text-center">
      {status === "loading" && <p>Verifying…</p>}
      {status === "ok" && <p className="text-teal-600">Signed in! Redirecting…</p>}
      {status === "fail" && <p className="text-red-600">{msg}</p>}
    </main>
  );
}
