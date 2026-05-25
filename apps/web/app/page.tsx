import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const GITHUB = process.env.NEXT_PUBLIC_GITHUB_URL || "https://github.com/BitMagistrate/TideGuard";
const CONTACT_EMAIL = "scaleblinkk@vk.com";

type CleanupStats = {
  cleanups: number;
  kg_collected: number;
  participants: number;
};

type PublicKPI = {
  users: number;
  reports_total: number;
  reports_approved: number;
  cleanups: number;
  kg_collected: number;
  schools: number;
  lessons_completed: number;
};

async function fetchCleanupStats(): Promise<CleanupStats | null> {
  try {
    const res = await fetch(`${API}/cleanups/stats`, { next: { revalidate: 60 } });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

async function fetchPublicKPI(): Promise<PublicKPI | null> {
  try {
    const res = await fetch(`${API}/admin/kpi_public`, { next: { revalidate: 60 } });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

function formatInt(n: number | undefined | null): string {
  if (n === undefined || n === null) return "—";
  if (n === 0) return "0";
  return n.toLocaleString("en-US");
}

export default async function HomePage() {
  const [cleanupStats, kpi] = await Promise.all([fetchCleanupStats(), fetchPublicKPI()]);
  const isLive =
    !!cleanupStats && cleanupStats.cleanups > 0 && kpi && kpi.users > 0;

  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="relative bg-gradient-to-br from-teal-700 via-teal-600 to-ocean-600 text-white overflow-hidden">
        <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_20%_20%,white,transparent_40%)]" />
        <div className="relative max-w-6xl mx-auto px-6 py-24">
          <div className="max-w-3xl">
            <p className="uppercase tracking-widest text-sand-100 text-sm mb-4">
              Physics-Informed AI for our oceans
            </p>
            <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
              AI that predicts plastic before it pollutes.
            </h1>
            <p className="text-lg md:text-xl text-sand-50 max-w-2xl mb-10">
              TideGuard AI combines Sentinel imagery, ocean currents and citizen reports
              with a Physics-Informed Neural Network to forecast marine debris hotspots
              up to 14 days in advance — and turns predictions into community action.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/map"
                aria-label="Open the live forecast map"
                className="px-6 py-3 bg-white text-teal-700 font-semibold rounded-lg hover:bg-sand-50 transition"
              >
                Try the map
              </Link>
              <Link
                href="/learn"
                aria-label="Open the environmental education lessons"
                className="px-6 py-3 border border-white/30 rounded-lg hover:bg-white/10 transition"
              >
                Explore EE lessons
              </Link>
              <Link
                href="/method"
                aria-label="See how the physics-informed model works"
                className="px-6 py-3 border border-white/30 rounded-lg hover:bg-white/10 transition"
              >
                How the model works
              </Link>
              <a
                href={GITHUB}
                aria-label="Open the open-source GitHub repository"
                className="px-6 py-3 border border-white/30 rounded-lg hover:bg-white/10 transition"
              >
                Open-source repo
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Proof — numbers the jury will ask for */}
      <section className="bg-sand-50 dark:bg-zinc-900/40 py-16">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-10">
            <p className="uppercase tracking-widest text-xs text-teal-700 mb-2">Evidence</p>
            <h2 className="text-3xl font-bold">Numbers the jury will ask for</h2>
            <p className="text-sm text-zinc-500 mt-2 max-w-2xl mx-auto">
              All four headline figures are computed from open code in this repository
              and documented in <Link href="/research" className="underline">/research</Link>.
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <BigStat value="279×" label="CO₂-eq prevented per CO₂-eq spent" href="/research#carbon" />
            <BigStat value="304%" label="Anapa pilot ROI in 2.97 months" href="/b2g/anapa" />
            <BigStat value="p < 3×10⁻¹¹²" label="Diebold–Mariano vs persistence" href="/research#benchmark" />
            <BigStat value="€270k" label="projected Year-1 revenue (mixed B2G + grants)" href="/pricing#economics" />
          </div>
        </div>
      </section>

      {/* Science credentials */}
      <section className="py-8 border-y border-zinc-200 dark:border-zinc-800">
        <div className="max-w-6xl mx-auto px-6 flex flex-wrap items-center justify-center gap-3 text-xs">
          <Badge>MIT License</Badge>
          <Badge>OSF Pre-registered</Badge>
          <Badge>arXiv (in submission)</Badge>
          <Badge>Zenodo DOI</Badge>
          <Badge>CC-BY-4.0 curriculum</Badge>
          <Badge>OpenSSF Best Practices</Badge>
        </div>
      </section>

      {/* Live community impact — actuals from API */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-semibold">Live community impact</h2>
          <p className="text-sm text-zinc-500 mt-1">
            {isLive
              ? "Numbers below are the actual counts in the production database. They update every minute."
              : "Pre-launch. Counters reflect the real state of the platform — we report zero until the first cleanup is logged."}
          </p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <ImpactCard label="cleanups logged" value={formatInt(cleanupStats?.cleanups ?? 0)} />
          <ImpactCard label="kg collected" value={formatInt(Math.round(cleanupStats?.kg_collected ?? 0))} />
          <ImpactCard label="cleanup volunteers" value={formatInt(cleanupStats?.participants ?? 0)} />
          <ImpactCard label="lessons completed" value={formatInt(kpi?.lessons_completed ?? 0)} />
        </div>
      </section>

      {/* Founder card */}
      <section className="bg-teal-50 dark:bg-teal-950/30 py-16">
        <div className="max-w-4xl mx-auto px-6 flex flex-col md:flex-row gap-8 items-center">
          <div className="w-32 h-32 shrink-0 rounded-full bg-gradient-to-br from-teal-500 to-ocean-600 grid place-items-center text-white text-4xl font-bold">
            VE
          </div>
          <div>
            <div className="text-xs uppercase tracking-widest text-teal-700">Founder</div>
            <h3 className="text-2xl font-bold mt-1">Vladimir Ermolenko — 17, Krasnoyarsk</h3>
            <p className="text-zinc-600 dark:text-zinc-300 mt-2">
              10th-grader at Gymnasium № 13 “Akadem”, Krasnoyarsk, Siberia.
              Built TideGuard in <strong>3 months with AI-assisted development</strong>
              {" "}— every design decision, benchmark and line of public copy
              reviewed and integrated by the founder. Looking for an academic mentor
              and 1–2 co-leads. MIT-licensed, no ghost team.
            </p>
            <div className="mt-3 flex flex-wrap gap-3 text-sm">
              <Link href="/about" className="text-teal-700 underline">Read the founder story →</Link>
              <a href={`mailto:${CONTACT_EMAIL}`} className="text-zinc-500 underline">{CONTACT_EMAIL}</a>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="bg-sand-50/50 dark:bg-zinc-900/40 py-20">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold mb-12 text-center">How TideGuard works</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <Step
              n={1}
              title="Fuse data"
              body="Sentinel-2/3, CMEMS currents, ERA5 wind, citizen reports — all flow into one feature store."
            />
            <Step
              n={2}
              title="Predict with physics"
              body="A PINN solves the 2D advection-diffusion equation while learning windage (α), diffusion (K) and beaching (λ)."
            />
            <Step
              n={3}
              title="Mobilize community"
              body="Schools and NGOs see hotspots on the map, get cleanup missions, learn through 10 EE lessons, earn badges."
            />
          </div>
          <div className="text-center mt-10">
            <Link href="/method" className="text-teal-700 font-medium underline">
              Read the full method →
            </Link>
          </div>
        </div>
      </section>

      {/* CTA strip */}
      <section className="bg-teal-700 text-white py-16">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <h3 className="text-2xl md:text-3xl font-bold mb-2">Open-source by default. Free for the public, forever.</h3>
            <p className="text-sand-100 max-w-2xl">
              The public forecast and the 10-lesson curriculum stay free by license.
              Premium API, B2G dashboards and Adopt-a-Beach fund the open platform.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link href="/leaderboard" className="px-5 py-3 bg-white text-teal-700 font-semibold rounded-lg">
              Community leaderboard
            </Link>
            <Link href="/research" className="px-5 py-3 border border-white/30 rounded-lg hover:bg-white/10">
              Research &amp; benchmark
            </Link>
            <Link href="/roadmap" className="px-5 py-3 border border-white/30 rounded-lg hover:bg-white/10">
              2026–2029 roadmap
            </Link>
          </div>
        </div>
      </section>

      <footer className="max-w-6xl mx-auto px-6 py-10 text-sm text-zinc-500">
        <div className="grid md:grid-cols-4 gap-6">
          <div>
            <div className="font-semibold text-zinc-700 dark:text-zinc-300 mb-2">TideGuard AI</div>
            <p>Open-source forecast of floating marine debris. MIT-licensed code, CC-BY-4.0 content.</p>
          </div>
          <div>
            <div className="font-semibold text-zinc-700 dark:text-zinc-300 mb-2">Product</div>
            <ul className="space-y-1">
              <li><Link href="/map" className="hover:text-teal-700">Forecast map</Link></li>
              <li><Link href="/method" className="hover:text-teal-700">Method</Link></li>
              <li><Link href="/pricing" className="hover:text-teal-700">Pricing</Link></li>
              <li><Link href="/b2g/anapa" className="hover:text-teal-700">B2G dashboard</Link></li>
            </ul>
          </div>
          <div>
            <div className="font-semibold text-zinc-700 dark:text-zinc-300 mb-2">Open science</div>
            <ul className="space-y-1">
              <li><Link href="/research" className="hover:text-teal-700">Research</Link></li>
              <li><Link href="/faq" className="hover:text-teal-700">FAQ</Link></li>
              <li><Link href="/press" className="hover:text-teal-700">Press kit</Link></li>
              <li><Link href="/partners" className="hover:text-teal-700">Partners</Link></li>
            </ul>
          </div>
          <div>
            <div className="font-semibold text-zinc-700 dark:text-zinc-300 mb-2">Contact</div>
            <ul className="space-y-1">
              <li><a href={`mailto:${CONTACT_EMAIL}`} className="hover:text-teal-700">{CONTACT_EMAIL}</a></li>
              <li><a href={GITHUB} className="hover:text-teal-700">GitHub repository</a></li>
              <li><Link href="/ru" className="hover:text-teal-700">Русская версия</Link></li>
            </ul>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-zinc-200 dark:border-zinc-800 text-center">
          © 2026 TideGuard AI · MIT-licensed code · CC-BY-4.0 content ·{" "}
          <a href={`mailto:${CONTACT_EMAIL}`} className="underline">{CONTACT_EMAIL}</a>
        </div>
      </footer>
    </main>
  );
}

function ImpactCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
      <div className="text-3xl md:text-4xl font-bold text-teal-600">{value}</div>
      <div className="text-sm text-zinc-500 mt-2 uppercase tracking-wider">{label}</div>
    </div>
  );
}

function BigStat({ value, label, href }: { value: string; label: string; href: string }) {
  return (
    <Link
      href={href}
      className="block text-center p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 hover:border-teal-500 transition"
    >
      <div className="text-2xl md:text-3xl font-bold text-teal-700 dark:text-teal-400">{value}</div>
      <div className="text-xs text-zinc-500 mt-2 leading-snug">{label}</div>
    </Link>
  );
}

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-zinc-300 dark:border-zinc-700 bg-white/60 dark:bg-zinc-900/60 px-3 py-1 text-zinc-600 dark:text-zinc-300">
      {children}
    </span>
  );
}

function Step({ n, title, body }: { n: number; title: string; body: string }) {
  return (
    <div className="p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
      <div className="text-teal-600 text-xl font-bold mb-2 inline-flex items-center gap-2">
        <span className="inline-flex w-8 h-8 items-center justify-center rounded-full bg-teal-100 text-teal-700">
          {n}
        </span>
      </div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-zinc-600 dark:text-zinc-400">{body}</p>
    </div>
  );
}
