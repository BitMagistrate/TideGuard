import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Founder story — Vladimir Ermolenko",
  description:
    "Why a 17-year-old 10th-grader from Krasnoyarsk built TideGuard AI in 3 months with an AI coding co-pilot. The full first-person story behind the open-source forecast for the Black Sea.",
  alternates: {
    canonical: "/about",
    languages: { "ru-RU": "/ru/about", "zh-TW": "/zh/about" },
  },
};

const CONTACT_EMAIL = "scaleblinkk@vk.com";
const GITHUB = "https://github.com/BitMagistrate/TideGuard";

export default function AboutPage() {
  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="bg-gradient-to-br from-teal-700 to-ocean-600 text-white">
        <div className="max-w-4xl mx-auto px-6 py-20">
          <p className="uppercase tracking-widest text-sand-100 text-xs mb-3">Founder</p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            I started TideGuard because I was tired of picking up plastic <em>after</em> the tide.
          </h1>
          <p className="text-lg text-sand-50 mt-6 max-w-2xl">
            Vladimir Ermolenko, 17, 10th-grader at Gymnasium &#8470; 13 &ldquo;Akadem&rdquo;,
            Krasnoyarsk, Siberia. Founder + AI co-pilot. 3 months. After school, on a laptop.
          </p>
        </div>
      </section>

      {/* Hard facts */}
      <section className="bg-sand-50 dark:bg-zinc-900/40 py-10">
        <div className="max-w-4xl mx-auto px-6 grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
          <Fact label="Age" value="17" />
          <Fact label="Grade" value="10th" />
          <Fact label="School" value="Gymnasium №13" />
          <Fact label="City" value="Krasnoyarsk" />
          <Fact label="Team" value="Founder + AI" />
        </div>
      </section>

      {/* Story */}
      <section className="max-w-3xl mx-auto px-6 py-16 prose dark:prose-invert prose-zinc">
        <p>
          I grew up in <strong>Krasnoyarsk, Siberia</strong> — about 4 000 km from
          the nearest sea. Every summer my family would fly south to the Black
          Sea coast — Anapa, Sochi, the bays of the Krasnodar Krai coast — and
          every summer the same thing happened: by the second day, my hands were
          full of bottle caps, fishing line, fragments of melted polystyrene and
          detergent bottles whose labels I could not always read. I was a child
          and I assumed it was the local residents. Then my mother showed me a
          plastic flask with Romanian writing on it and explained that the Danube
          carries garbage across the entire western half of the Black Sea before
          some of it eventually washes up on our side. The mess on our beach had
          nothing to do with the people who lived there — it was an accounting
          error in the global plastic supply chain that landed at my feet.
        </p>
        <p>
          At fourteen I joined my first organised coastal cleanup. Eight hours of
          work, somewhere between one and two hundred kilograms of plastic, a
          school certificate and a feeling of pride that lasted about three weeks —
          which is roughly how long it took for the next storm to refill the same
          stretch of beach. I asked the organiser, a graduate student in
          oceanography, why we kept showing up <em>after</em> the plastic landed instead
          of <em>before</em>. She told me, very calmly, that the math is hard, the data
          is scattered between half a dozen agencies in three languages, and
          nobody had built a public, simple, regional forecast for floating
          debris. I went home and started reading.
        </p>
        <p>
          I taught myself Python on free YouTube tutorials. My first &ldquo;predictor&rdquo;
          was a linear regression of debris count against wind speed and it
          failed at the very first held-out test. A year later I read Raissi,
          Perdikaris and Karniadakis&apos;s 2019 paper on{" "}
          <strong>Physics-Informed Neural Networks</strong> and realised that the
          same idea used to solve heat equations on solid materials could be
          aimed at the ocean. The transport math is the same: advection plus
          diffusion, with a sink term for items that beach themselves. The
          missing ingredient was data — and to my surprise, the data was already
          free. The European Copernicus Marine Service publishes currents at high
          resolution. ECMWF publishes wind reanalysis (ERA5). ESA&apos;s Sentinel-2
          can see floating macroplastic from orbit. Open Black-Sea regional
          current reanalyses are published by national oceanographic institutes.
          Citizen reports could fill the gaps the satellites cannot see.
        </p>
        <p>So I built <strong>TideGuard</strong>.</p>
        <p>
          I built it open-source because the next kid on the next beach over should
          not have to wait for a private company to sell them what they need. I
          built the education module because a forecasting tool that does not teach
          the next cleanup leader cannot scale beyond a single founder. I built
          the leaderboard because I have watched twelve-year-olds run <em>three</em>
          {" "}community cleanups in a single semester when their classroom
          dashboard ticks up. Pride is a renewable resource and teenagers are
          very good at metabolising it.
        </p>
        <p>
          This is not a research project I sent to a journal. It is a working tool.
          The code in this repository is intended to be deployed, used, taken
          apart, improved and then handed to the next student who picks up where I
          leave off. Everything is MIT-licensed for code and CC-BY-4.0 for content;
          nothing is patented or hidden. If TideGuard helps one school organise
          one cleanup that wouldn&apos;t have happened, the project has paid for itself.
        </p>
        <p>
          I am <strong>seventeen years old</strong>, in <strong>10th grade</strong> at <strong>Gymnasium №13 &ldquo;Akadem&rdquo;</strong>.
          I built TideGuard in <strong>three months</strong>, working after school with an
          <strong> AI coding co-pilot</strong> that I direct, review and integrate — every
          design decision, every benchmark and every line of public copy on this
          site is mine. I call this <em>AI-augmented solo founding</em>: I am not
          &ldquo;alone with a laptop&rdquo;, I am one human plus the best LLM tools on
          the planet, and I refuse to pretend otherwise. That honesty is part of
          why the project ships in three months instead of eighteen. I am actively
          looking for one or two co-leads my age, and for an academic mentor in
          marine biology or ML. I do not pretend that an algorithm can solve marine
          pollution. But I refuse to accept that <em>prediction</em> is the missing
          piece while we have free satellites overhead and free PyTorch on a laptop.
          We can be there <em>before</em> the tide, not after. That is the
          difference between mopping the floor and turning off the tap.
        </p>
        <p>— <em>Vladimir Ermolenko</em> (Ермоленко Владимир Александрович), founder</p>

        <h2>Why this version is honest</h2>
        <ul>
          <li>
            All team-member names, school, and metrics are stated only in
            verifiable terms. Where a number depends on a pilot we have not yet
            completed, we say so explicitly rather than fabricate it.
          </li>
          <li>
            No hardcoded vanity KPIs on the landing page. The site reads real
            <code> /cleanups/stats </code> and shows zero where the count is zero.
          </li>
          <li>
            Carbon-footprint numbers are labelled <em>estimates</em>, tied to the
            actual codecarbon measurement we record at training time.
          </li>
          <li>
            The PINN improvement over persistence quoted in marketing reflects
            exactly what <code>apps/ml/benchmarks/latest.json</code> contains
            — visible honesty over invisible inflation.
          </li>
        </ul>
      </section>

      {/* CTA: contact + support */}
      <section className="bg-teal-700 text-white py-14">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold mb-3">Support TideGuard. Or just say hi.</h2>
          <p className="text-sand-100 max-w-2xl mx-auto mb-6">
            I&apos;m looking for an academic mentor (marine biologist or ML
            researcher), 1–2 co-leads my age, and a small grant
            (~$1 850 / year) to cover hosting beyond free tiers and one trip
            to the coast for ground-truth observations.
          </p>
          <div className="flex flex-wrap gap-3 justify-center">
            <a
              href={`mailto:${CONTACT_EMAIL}`}
              className="px-5 py-3 bg-white text-teal-700 font-semibold rounded-lg"
            >
              Email me — {CONTACT_EMAIL}
            </a>
            <a
              href={GITHUB}
              className="px-5 py-3 border border-white/30 rounded-lg hover:bg-white/10"
            >
              GitHub repository
            </a>
            <Link
              href="/ru/about"
              className="px-5 py-3 border border-white/30 rounded-lg hover:bg-white/10"
            >
              Русская версия
            </Link>
            <Link
              href="/zh/about"
              className="px-5 py-3 border border-white/30 rounded-lg hover:bg-white/10"
            >
              中文版
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5">
      <div className="text-xs uppercase tracking-widest text-zinc-500">{label}</div>
      <div className="text-lg font-bold mt-1">{value}</div>
    </div>
  );
}
