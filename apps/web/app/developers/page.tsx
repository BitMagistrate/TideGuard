"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

type Endpoint = {
  method: string;
  path: string;
  summary: string;
  example: string;
};

type Portal = {
  title: string;
  status: string;
  base_url: string;
  auth: { header: string; enforcement: string; request_a_key: string };
  rate_limits: { anonymous: string; with_key: string };
  endpoints: Endpoint[];
  openapi: string;
  github: string;
  zenodo: string;
};

export default function DevelopersPage() {
  const [portal, setPortal] = useState<Portal | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const url = `${API_URL}/developers`;
    fetch(url)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`${r.status} ${r.statusText}`))))
      .then(setPortal)
      .catch((e) => setError(String(e)));
  }, []);

  if (error)
    return (
      <main className="mx-auto max-w-4xl p-8">
        <h1 className="text-3xl font-bold mb-4">Developer Portal</h1>
        <p className="text-red-700">Could not contact the API: {error}</p>
      </main>
    );

  if (!portal)
    return (
      <main className="mx-auto max-w-4xl p-8">
        <h1 className="text-3xl font-bold mb-4">Developer Portal</h1>
        <p>Loading…</p>
      </main>
    );

  return (
    <main className="mx-auto max-w-4xl p-8 space-y-8">
      <header>
        <h1 className="text-3xl font-bold mb-2">{portal.title}</h1>
        <p className="text-sm text-gray-600">
          Status: <strong>{portal.status}</strong> · Base URL:{" "}
          <code>{portal.base_url}</code>
        </p>
      </header>

      <section className="rounded-lg border border-gray-200 p-5">
        <h2 className="text-xl font-semibold mb-3">Authentication</h2>
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <dt className="text-sm font-medium text-gray-500">Header</dt>
            <dd><code>{portal.auth.header}</code></dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Enforcement</dt>
            <dd>{portal.auth.enforcement}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Request a key</dt>
            <dd>
              <a className="text-blue-700 underline" href={portal.auth.request_a_key}>
                scaleblinkk@vk.com
              </a>
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Rate limit</dt>
            <dd>
              {portal.rate_limits.anonymous} · with key: {portal.rate_limits.with_key}
            </dd>
          </div>
        </dl>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-3">Endpoints</h2>
        <ul className="space-y-4">
          {portal.endpoints.map((ep) => (
            <li
              key={`${ep.method}-${ep.path}`}
              className="rounded-lg border border-gray-200 p-4"
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-800">
                  {ep.method}
                </span>
                <code className="text-sm font-mono">{ep.path}</code>
              </div>
              <p className="text-sm text-gray-700 mb-2">{ep.summary}</p>
              <pre className="bg-gray-900 text-gray-100 text-xs rounded p-3 overflow-auto">
                {ep.example}
              </pre>
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-lg border border-gray-200 p-5">
        <h2 className="text-xl font-semibold mb-3">Resources</h2>
        <ul className="list-disc pl-6 space-y-1">
          <li>
            <a className="text-blue-700 underline" href={portal.openapi}>
              OpenAPI spec
            </a>
          </li>
          <li>
            <a className="text-blue-700 underline" href={portal.github}>
              Source on GitHub
            </a>
          </li>
          <li>
            <a className="text-blue-700 underline" href={`https://doi.org/${portal.zenodo}`}>
              Zenodo DOI: {portal.zenodo}
            </a>
          </li>
        </ul>
      </section>
    </main>
  );
}
