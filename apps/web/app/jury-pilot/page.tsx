import Link from "next/link";
import JuryTour from "@/components/JuryTour";

export const metadata = {
  title: "TideGuard AI · Juror walkthrough",
  description:
    "A 5-minute tour for jurors, journalists and mentors: see what TideGuard does, why it's honest, and where to verify every claim.",
};

export default function JuryPilotPage() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
        Juror walkthrough · 5 minutes
      </h1>
      <p className="mt-4 text-base leading-7 text-slate-700 dark:text-slate-300">
        Welcome. This page is the &quot;auditor entry point&quot; into TideGuard.
        Click the cyan button in the bottom-right (or
        <button
          form="jury-tour-form"
          className="mx-1 underline text-cyan-700 hover:text-cyan-500"
          type="submit"
        >
          press space
        </button>
        ) to start the tour. Every step links to evidence inside the repository.
      </p>
      <ul className="mt-8 space-y-3 text-sm text-slate-700 dark:text-slate-300">
        <li>
          <Link href="/method" className="text-cyan-700 underline">
            Read the model card →
          </Link>
        </li>
        <li>
          <Link href="/research/preregistration" className="text-cyan-700 underline">
            Read the OSF pre-registration →
          </Link>
        </li>
        <li>
          <Link href="/learn" className="text-cyan-700 underline">
            Browse the 10 open-source lessons →
          </Link>
        </li>
        <li>
          <a
            href="https://github.com/BitMagistrate/TideGuard"
            target="_blank"
            rel="noreferrer"
            className="text-cyan-700 underline"
          >
            View the source repository →
          </a>
        </li>
      </ul>
      <JuryTour autoStart />
    </main>
  );
}
