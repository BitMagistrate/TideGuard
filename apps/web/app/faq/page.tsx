"use client";

import { useState } from "react";
import Link from "next/link";

type QA = { q: string; a: React.ReactNode };

const FAQS: QA[] = [
  {
    q: "What if the PINN doesn't actually beat persistence on real data?",
    a: (
      <>
        <p>
          That&apos;s exactly what the pre-registered acceptance rule on OSF is for.
          The rule is: PINN beats baseline if and only if Diebold–Mariano{" "}
          <code>p &lt; 0.05</code> <em>and</em> the bootstrap 95% CI on the
          RMSE-difference is strictly negative. If either fails on the real-data
          run scheduled for summer 2026, we publish the negative result and we
          ship the baseline.
        </p>
        <p className="mt-2">
          A negative result does <em>not</em> kill the project. The platform —
          map, lessons, citizen reports, B2G dashboard — works on top of any
          forecast model, including the analytic Lagrangian baseline.
        </p>
      </>
    ),
  },
  {
    q: "How do we know you didn't tune the model to make the numbers look good?",
    a: (
      <p>
        Because the success rule was pre-registered on OSF <em>before</em> the
        real-data run, and the benchmark is reproducible by anyone in ~10 minutes
        with one command — see <Link href="/research#benchmark" className="underline">/research</Link>.
        All training and evaluation code is MIT-licensed in the repository.
      </p>
    ),
  },
  {
    q: "Why PINN and not a regular deep-learning model?",
    a: (
      <p>
        A pure data-driven network has nothing to lean on outside the training
        distribution. The PDE residual term in the loss forces the network to
        respect mass conservation and transport physics, which is what makes
        the model extrapolate to fresh storms and unfamiliar coastal segments.
        Pure ML models we tried overfit the synthetic data noise; PINN does not.
      </p>
    ),
  },
  {
    q: "What happens when the founder leaves for university?",
    a: (
      <p>
        Everything is open-source, MIT-licensed, with a public roadmap and CI
        running on every commit. The project is designed for continuity:
        contribution guide in <code>CONTRIBUTING.md</code>, governance notes in{" "}
        <code>docs/scaling_plan_2026_2029.md</code>. I am actively recruiting two
        co-leads my own age right now precisely so the project does not depend
        on me. The platform is portable to a new maintainer in a weekend.
      </p>
    ),
  },
  {
    q: "Who are you to compete with The Ocean Cleanup and Plastic Drift?",
    a: (
      <p>
        We aren&apos;t competing — those projects do different things. The Ocean
        Cleanup removes plastic in the open ocean, Plastic Drift maps global
        trajectories, Global Plastic Watch flags land-side dumps from satellite.
        None of them ship a public, regional, uncertainty-aware Black Sea
        forecast paired with a free K-12 curriculum and a B2G dashboard. That
        gap is what TideGuard fills.
      </p>
    ),
  },
  {
    q: "How do you comply with 152-ФЗ (Russia) and GDPR?",
    a: (
      <p>
        Citizen reports are pseudonymous by design. We store only the
        information needed for forecasting: rough coordinates, photo hash and
        a generic device fingerprint. Data ethics policy:{" "}
        <code>docs/DATA_ETHICS.md</code>; GDPR compliance notes:{" "}
        <code>docs/GDPR_COMPLIANCE.md</code>. All EU personal data is processed
        on EU-hosted infrastructure with one-click data deletion.
      </p>
    ),
  },
  {
    q: "What if you lose access to Sentinel or CMEMS due to sanctions?",
    a: (
      <p>
        We have a documented contingency: switch to a degraded mode using only
        ERA5 and open AIS / ship-of-opportunity observations until the official
        feeds return. The risk register at <code>docs/risk_register.md</code>{" "}
        spells out three independent failure paths and the corresponding fallback
        models.
      </p>
    ),
  },
  {
    q: "Are you really a founder + AI co-pilot?",
    a: (
      <p>
        Yes. There is no ghost team, no agency, no parent organisation. I am
        17 years old, I built the codebase alone in 3 months on a single
        laptop, and I have not paid or been paid by anyone for this work. I am
        looking for one or two co-leads my age and an academic mentor — see{" "}
        <Link href="/about" className="underline">/about</Link>.
      </p>
    ),
  },
  {
    q: "Is this profitable?",
    a: (
      <p>
        No, and we never claim it is. TideGuard is pre-revenue. The pricing
        page shows projected unit economics — Year-1 blended revenue is{" "}
        <em>projected</em> at €270k from B2G subscriptions and grants. The
        public forecast and the EE curriculum will stay free by license,
        regardless of paid-tier outcomes.
      </p>
    ),
  },
];

export default function FAQPage() {
  return (
    <main className="min-h-screen">
      <section className="bg-gradient-to-br from-teal-700 to-ocean-600 text-white">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <p className="uppercase tracking-widest text-sand-100 text-xs mb-3">
            Hard questions
          </p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            Answers to the questions the jury would actually ask.
          </h1>
          <p className="text-lg text-sand-50 mt-6 max-w-3xl">
            We answer the uncomfortable ones up front — pre-registration, fallback
            models, continuity, governance and how we know we&apos;re not just
            picking ourselves with the benchmark.
          </p>
        </div>
      </section>

      <section className="max-w-3xl mx-auto px-6 py-16 space-y-3">
        {FAQS.map((qa, i) => (
          <FAQItem key={i} qa={qa} />
        ))}
      </section>

      <section className="bg-sand-50 dark:bg-zinc-900/40 py-14">
        <div className="max-w-3xl mx-auto px-6 text-center text-sm text-zinc-600 dark:text-zinc-400">
          Still want to ask a harder one? Email{" "}
          <a href="mailto:scaleblinkk@vk.com" className="underline">scaleblinkk@vk.com</a> —
          replies in 48 hours.
        </div>
      </section>
    </main>
  );
}

function FAQItem({ qa }: { qa: QA }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-3 px-5 py-4 text-left"
        aria-expanded={open}
      >
        <span className="font-semibold">{qa.q}</span>
        <span className="text-teal-700 text-xl shrink-0">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <div className="px-5 pb-5 text-zinc-700 dark:text-zinc-300 leading-relaxed text-[15px]">
          {qa.a}
        </div>
      )}
    </div>
  );
}
