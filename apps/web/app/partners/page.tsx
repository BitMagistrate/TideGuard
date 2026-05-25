import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Partners & network",
  description:
    "TideGuard AI ecosystem: data providers, cloud sponsors, schools, NGOs and academic mentors. We mark every partner with an honest active / in-discussion status.",
  alternates: { canonical: "/partners" },
};

const CONTACT_EMAIL = "scaleblinkk@vk.com";

type Partner = { name: string; status: "active" | "in-discussion"; blurb?: string };

type Category = { title: string; intro: string; items: Partner[] };

const CATEGORIES: Category[] = [
  {
    title: "Data providers",
    intro:
      "Open scientific data sources that feed the PINN. All currently used today.",
    items: [
      { name: "Copernicus Marine Service (CMEMS)", status: "active", blurb: "Black Sea currents reanalysis" },
      { name: "ECMWF ERA5", status: "active", blurb: "10 m wind reanalysis" },
      { name: "ESA Sentinel-2", status: "active", blurb: "Satellite macro-plastic detection" },
      { name: "NEMO Black-Sea regional model (CMEMS)", status: "active", blurb: "Open regional current reanalyses" },
      { name: "NOAA OISST", status: "active", blurb: "Sea-surface temperature" },
      { name: "Open-Meteo Marine API", status: "active", blurb: "Stokes drift (roadmap)" },
    ],
  },
  {
    title: "Cloud & infrastructure sponsors",
    intro:
      "Sponsorship applications have been submitted to several providers. We mark each with its real, current status.",
    items: [
      { name: "Cloudflare (Project Galileo)", status: "in-discussion" },
      { name: "Vercel — OSS plan", status: "active", blurb: "Web hosting (free tier today)" },
      { name: "Fly.io — Hobby plan", status: "active", blurb: "API hosting (free tier today)" },
      { name: "Neon Postgres", status: "in-discussion" },
      { name: "GitHub Education", status: "in-discussion" },
      { name: "Sentry for OSS", status: "in-discussion" },
    ],
  },
  {
    title: "Academic & research",
    intro:
      "Researchers we have reached out to with templated, open letters of support. None have signed yet — founder + AI co-pilot, pre-revenue.",
    items: [
      { name: "Prof. Erik van Sebille (Utrecht)", status: "in-discussion", blurb: "Particle tracking & marine plastic" },
      { name: "Prof. Atsuhiko Isobe (Kyushu)", status: "in-discussion", blurb: "Floating debris quantification" },
      { name: "Russian Academy of Sciences — Marine Institute", status: "in-discussion" },
      { name: "Sirius University", status: "in-discussion" },
    ],
  },
  {
    title: "Schools & NGOs",
    intro:
      "Schools and NGOs we are in conversation with about pilot lessons and cleanup events. No signed MoU yet.",
    items: [
      { name: "Gymnasium №13 «Akadem», Krasnoyarsk", status: "active", blurb: "Founder's school, first lesson pilot" },
      { name: "Gymnasium of Anapa", status: "in-discussion" },
      { name: "«Чистые игры» (RU clean-up NGO)", status: "in-discussion" },
      { name: "Russian Geographical Society — youth chapter", status: "in-discussion" },
      { name: "ЭКА green movement", status: "in-discussion" },
    ],
  },
];

export default function PartnersPage() {
  return (
    <main className="min-h-screen">
      <section className="bg-gradient-to-br from-teal-700 to-ocean-600 text-white">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <p className="uppercase tracking-widest text-sand-100 text-xs mb-3">Partners</p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            Who we work with. Who we want to work with.
          </h1>
          <p className="text-lg text-sand-50 mt-6 max-w-3xl">
            We separate <strong>active</strong> partners from <strong>in-discussion</strong>{" "}
            ones with a clear badge — no inflated logo walls. Want to become an
            endorser? <a href={`mailto:${CONTACT_EMAIL}`} className="underline">Email us</a>.
          </p>
        </div>
      </section>

      {CATEGORIES.map((c) => (
        <section key={c.title} className="max-w-5xl mx-auto px-6 py-12">
          <h2 className="text-2xl font-bold">{c.title}</h2>
          <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">{c.intro}</p>
          <div className="grid md:grid-cols-2 gap-4 mt-6">
            {c.items.map((p) => (
              <div
                key={p.name}
                className="flex items-start justify-between gap-3 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-4"
              >
                <div>
                  <div className="font-semibold">{p.name}</div>
                  {p.blurb && <div className="text-sm text-zinc-500 mt-1">{p.blurb}</div>}
                </div>
                <StatusBadge status={p.status} />
              </div>
            ))}
          </div>
        </section>
      ))}

      <section className="bg-teal-700 text-white py-14">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold mb-3">Endorse TideGuard.</h2>
          <p className="text-sand-100 mb-6">
            We publish every signed letter of support at <code>docs/letters_of_support/</code>.
            A 1-page letter template is in the repo — feel free to fork it.
          </p>
          <a
            href={`mailto:${CONTACT_EMAIL}?subject=Letter%20of%20Support%20%E2%80%94%20TideGuard%20AI`}
            className="inline-block px-5 py-3 bg-white text-teal-700 font-semibold rounded-lg"
          >
            Email us — {CONTACT_EMAIL}
          </a>
        </div>
      </section>
    </main>
  );
}

function StatusBadge({ status }: { status: "active" | "in-discussion" }) {
  if (status === "active") {
    return (
      <span className="shrink-0 inline-flex items-center rounded-full bg-teal-100 text-teal-700 text-xs px-2 py-0.5">
        Active
      </span>
    );
  }
  return (
    <span className="shrink-0 inline-flex items-center rounded-full bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300 text-xs px-2 py-0.5">
      In discussion
    </span>
  );
}
