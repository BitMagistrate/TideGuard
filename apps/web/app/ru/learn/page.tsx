import type { Metadata } from "next";
import LearnPage from "../../learn/page";

export const metadata: Metadata = {
  title: "Экологическое образование — TideGuard AI",
  description:
    "10 уроков на русском о морском пластике, океанической физике и гражданской науке, согласованных с программой средней школы.",
  alternates: {
    canonical: "/ru/learn",
    languages: { "en-US": "/learn", "zh-TW": "/zh/learn" },
  },
};

export default async function RuLearnPage() {
  // Reuse the canonical LearnPage server component with Russian preselected.
  return await LearnPage({ searchParams: { lang: "ru" } });
}
