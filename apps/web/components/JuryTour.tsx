"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Lightweight scripted juror tour for `/jury-pilot`.
 *
 * Renders an overlay that walks a juror through 6 high-signal facts
 * about the project in ≤ 5 minutes:
 *
 *   1. Why this exists — the 72-hour rainfall-to-plastic window.
 *   2. How it works — PINN with three physical parameters.
 *   3. What it predicts — concentration map + probability-of-exceed.
 *   4. The pre-registered acceptance rule on OSF.
 *   5. The 10-lesson curriculum (CC-BY-4.0).
 *   6. Where to look in the repository for proof.
 *
 * Self-contained — no external dependency on driver.js or reactour
 * so that the bundle stays tiny.
 */

type Step = {
  title: string;
  body: string;
  cta?: { label: string; href: string };
};

const STEPS: Step[] = [
  {
    title: "Why TideGuard exists",
    body:
      "After rainfall on the Black Sea coast, floating plastic typically reaches beaches in ~72 hours. " +
      "If volunteers can intercept it during that window, removal costs USD 5/kg instead of USD 100/kg in open water. " +
      "TideGuard's job is to make that window predictable and open.",
  },
  {
    title: "How the model works",
    body:
      "A Physics-Informed Neural Network (PINN) solves the advection-diffusion equation with three learnable physical parameters: " +
      "windage α, eddy diffusion K, and beaching rate λ. The PDE residual is part of the loss — the model is physically constrained, not unconstrained.",
    cta: { label: "Read the model card", href: "/method" },
  },
  {
    title: "What you see on the map",
    body:
      "Each tile shows mean predicted concentration and the probability that concentration will exceed a user-defined threshold within the next 24h–14d window. " +
      "Tile colour = mean. Tile opacity = probability of exceedance. Tap any tile for full details.",
  },
  {
    title: "Pre-registered honesty",
    body:
      "The real-data acceptance rule is publicly registered on OSF: " +
      "Diebold–Mariano p < 0.05 AND 95% bootstrap CI upper bound < 0. " +
      "If the model fails the rule, the platform sunsets the ML component rather than pretending.",
    cta: { label: "Read the OSF preregistration", href: "/research/preregistration" },
  },
  {
    title: "Curriculum, not just an app",
    body:
      "10 K-12 lessons aligned with the Russian FGOS 5-9 standard, free to use under CC-BY-4.0. " +
      "Schools can print them. Teachers can modify them. Students get PDF certificates after completing the course.",
    cta: { label: "Browse the lessons", href: "/learn" },
  },
  {
    title: "Where to verify each claim",
    body:
      "Every assertion you saw is verifiable inside the repository. Source: github.com/BitMagistrate/TideGuard. " +
      "Live API: api.tideguard.app/docs. Status: status.tideguard.app. Welcome to TideGuard.",
    cta: { label: "Open the repository", href: "https://github.com/BitMagistrate/TideGuard" },
  },
];

interface JuryTourProps {
  /** If true, the tour starts automatically on mount. */
  autoStart?: boolean;
}

export default function JuryTour({ autoStart = false }: JuryTourProps) {
  const [open, setOpen] = useState(false);
  const [idx, setIdx] = useState(0);
  const triggered = useRef(false);

  useEffect(() => {
    if (autoStart && !triggered.current) {
      triggered.current = true;
      setOpen(true);
    }
  }, [autoStart]);

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 rounded-full bg-cyan-600 px-4 py-2 text-sm font-medium text-white shadow-lg hover:bg-cyan-500"
        aria-label="Take the juror tour"
      >
        ▶ Juror tour (5 min)
      </button>
    );
  }

  const step = STEPS[idx];
  const last = idx === STEPS.length - 1;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="jury-tour-title"
    >
      <div className="max-w-lg rounded-lg bg-white p-6 shadow-2xl dark:bg-slate-900">
        <header className="mb-3 flex items-center justify-between">
          <h2 id="jury-tour-title" className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            {idx + 1}. {step.title}
          </h2>
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="text-slate-500 hover:text-slate-900 dark:hover:text-slate-100"
            aria-label="Close juror tour"
          >
            ✕
          </button>
        </header>
        <p className="text-sm leading-6 text-slate-700 dark:text-slate-300">{step.body}</p>
        {step.cta ? (
          <a
            href={step.cta.href}
            className="mt-4 inline-block text-sm text-cyan-700 underline hover:text-cyan-500"
            target={step.cta.href.startsWith("http") ? "_blank" : undefined}
            rel="noreferrer"
          >
            {step.cta.label} →
          </a>
        ) : null}
        <footer className="mt-6 flex items-center justify-between text-xs text-slate-500">
          <span>
            Step {idx + 1} of {STEPS.length}
          </span>
          <div className="space-x-2">
            <button
              type="button"
              onClick={() => setIdx(Math.max(0, idx - 1))}
              className="rounded border border-slate-300 px-3 py-1 disabled:opacity-50"
              disabled={idx === 0}
            >
              Back
            </button>
            {last ? (
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="rounded bg-cyan-600 px-3 py-1 text-white"
              >
                Finish
              </button>
            ) : (
              <button
                type="button"
                onClick={() => setIdx(idx + 1)}
                className="rounded bg-cyan-600 px-3 py-1 text-white"
              >
                Next
              </button>
            )}
          </div>
        </footer>
      </div>
    </div>
  );
}
