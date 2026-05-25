import Link from "next/link";

export default function DashboardHome() {
  return (
    <main className="max-w-5xl mx-auto px-6 py-16">
      <h1 className="text-3xl font-bold">Developer dashboard</h1>
      <p className="text-zinc-500 mt-2">
        Manage your API keys, monitor usage and switch between tiers.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-10">
        <Card href="/dashboard/api-keys" title="API keys" blurb="Create, rotate and revoke keys for your applications." />
        <Card href="/dashboard/usage" title="Usage" blurb="Daily request counts per endpoint, rate-limit headers." />
        <Card href="/dashboard/billing" title="Billing" blurb="Current tier, invoices, payment method." />
      </div>
    </main>
  );
}

function Card({ href, title, blurb }: { href: string; title: string; blurb: string }) {
  return (
    <Link href={href} className="block rounded-xl border border-zinc-200 p-5 hover:shadow-md">
      <div className="font-semibold">{title}</div>
      <div className="text-sm text-zinc-500 mt-1">{blurb}</div>
    </Link>
  );
}
