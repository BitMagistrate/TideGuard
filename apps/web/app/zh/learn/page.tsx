import type { Metadata } from "next";
import LearnPage from "../../learn/page";

export const metadata: Metadata = {
  title: "環境教育 — TideGuard AI",
  description: "10 堂關於海洋塑膠、海洋物理與公民科學的中文課程,符合中學課綱。",
  alternates: {
    canonical: "/zh/learn",
    languages: { "en-US": "/learn", "ru-RU": "/learn?lang=ru" },
  },
};

export default async function ZhLearnPage() {
  // Reuse the canonical LearnPage server component with zh-TW preselected.
  return await LearnPage({ searchParams: { lang: "zh-TW" } });
}
