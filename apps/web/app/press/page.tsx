import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Press kit",
  description:
    "Boilerplate, ready-to-quote abstracts, key figures and brand assets for journalists covering TideGuard AI.",
  alternates: { canonical: "/press" },
};

const CONTACT_EMAIL = "scaleblinkk@vk.com";
const GITHUB = "https://github.com/BitMagistrate/TideGuard";

export default function PressPage() {
  return (
    <main className="min-h-screen">
      <section className="bg-gradient-to-br from-teal-700 to-ocean-600 text-white">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <p className="uppercase tracking-widest text-sand-100 text-xs mb-3">Press kit</p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            Quote us correctly. Quote us freely.
          </h1>
          <p className="text-lg text-sand-50 mt-6 max-w-3xl">
            All content on this page is CC-BY-4.0 — use it in articles,
            newsletters, school newspapers. Press contact:{" "}
            <a href={`mailto:${CONTACT_EMAIL}`} className="underline">{CONTACT_EMAIL}</a>.
          </p>
        </div>
      </section>

      {/* Elevator pitches */}
      <section className="max-w-5xl mx-auto px-6 py-16 space-y-12">
        <Block title="60-word elevator pitch">
          <p>
            TideGuard AI is an open-source forecast of floating plastic on the
            Black Sea coast. A physics-informed neural network combines
            satellite imagery, ocean currents and citizen reports to predict
            debris hotspots 48 to 72 hours before the tide. The platform is
            free for the public, MIT-licensed, and built with an AI coding co-pilot by a 17-year-old
            from Krasnoyarsk, Russia.
          </p>
        </Block>

        <Block title="120-word abstract">
          <p>
            TideGuard AI is the first regional, open-science forecast of
            floating marine debris on the Black Sea. The model solves a 2D
            advection–diffusion equation for surface plastic concentration
            using a Physics-Informed Neural Network: windage, eddy diffusion
            and the beaching rate are learned directly from data. On a
            five-seed synthetic benchmark the PINN beats persistence with{" "}
            <code>p &lt; 3×10⁻¹¹²</code> (Diebold–Mariano) at a 14-day horizon.
            The platform pairs the forecast with a free 10-lesson curriculum
            in English, Russian and Chinese and a B2G dashboard for
            municipalities. Built solo by Vladimir Ermolenko (17,
            Krasnoyarsk), MIT-licensed, OSF pre-registered, no patents.
          </p>
        </Block>

        <Block title="Key figures (free to quote)">
          <ul className="list-disc pl-6 space-y-1">
            <li>PINN: RMSE 0.0929, NSE 0.913 on synthetic Black Sea problem.</li>
            <li>Beats persistence baseline by 7.6% RMSE, Lagrangian by 4.4%.</li>
            <li>Statistical significance: <code>p &lt; 3 × 10⁻¹¹²</code> (Diebold–Mariano).</li>
            <li>540+ one-kilometre beach segments across 22 cities.</li>
            <li>10 lessons × 3 languages = 30 lesson modules.</li>
            <li>Training carbon: 0.12 kg CO₂e; predicted prevention ratio ≈ 279×.</li>
            <li>Anapa pilot ROI projection: 304% in 2.97 months.</li>
            <li>Founder + AI, MIT code, CC-BY-4.0 lessons.</li>
          </ul>
        </Block>

        <Block title="Founder">
          <p>
            <strong>Vladimir Ermolenko</strong> (Ермоленко Владимир Александрович),
            17, 10th grade at Gymnasium №13 «Akadem» in Krasnoyarsk. Built TideGuard
            in 3 months with an AI co-pilot. Available for interviews in Russian or English.
          </p>
          <p className="mt-2">
            Full founder story: <Link href="/about" className="underline">/about</Link>{" "}
            (EN) · <Link href="/ru/about" className="underline">/ru/about</Link> (RU).
          </p>
        </Block>

        <Block title="Brand assets">
          <ul className="list-disc pl-6 space-y-1">
            <li>Open-graph card: <code>/og-image.png</code> (1200×630)</li>
            <li>Favicon: <code>/favicon.ico</code></li>
            <li>Primary teal: <code>#0b5550</code> · Ocean blue: <code>#025980</code> · Sand: <code>#FEF8E7</code></li>
            <li>Repository: <a href={GITHUB} className="underline">{GITHUB}</a></li>
          </ul>
        </Block>

        <Block title="Boilerplate (1-paragraph, for the &ldquo;About&rdquo; section of an article)">
          <p>
            TideGuard AI is an open-source platform that forecasts floating
            marine plastic on the Black Sea coast 48 to 72 hours before it
            beaches, using a physics-informed neural network on top of free
            satellite and oceanographic data. The platform combines a public
            map, a 10-lesson curriculum in three languages and a municipal
            dashboard. It is MIT-licensed for code and CC-BY-4.0 for content,
            with all benchmarks reproducible from a single command. TideGuard
            was built with an AI coding co-pilot by 17-year-old Vladimir Ermolenko (Krasnoyarsk,
            Russia) and is pre-registered on the Open Science Framework.
          </p>
        </Block>
      </section>

      <section className="bg-teal-700 text-white py-14">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold mb-3">Need a quote, an interview, or raw data?</h2>
          <p className="text-sand-100 mb-6">
            Replies within 48 hours, English or Russian. Mention your outlet and
            deadline in the subject line.
          </p>
          <a
            href={`mailto:${CONTACT_EMAIL}?subject=Press%20enquiry%20%E2%80%94%20TideGuard%20AI`}
            className="inline-block px-5 py-3 bg-white text-teal-700 font-semibold rounded-lg"
          >
            {CONTACT_EMAIL}
          </a>
        </div>
      </section>
    </main>
  );
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
      <h2 className="text-xl font-semibold">{title}</h2>
      <div className="mt-3 text-zinc-700 dark:text-zinc-300 leading-relaxed">{children}</div>
    </div>
  );
}
