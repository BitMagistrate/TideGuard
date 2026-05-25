import Link from "next/link";
import type { Metadata } from "next";
import ZhTranslationNotice from "../../../components/Lang/ZhTranslationNotice";

export const metadata: Metadata = {
  title: "路線圖 — 接下來會建構什麼",
  description: "TideGuard AI 的公開路線圖,包含里程碑與已知缺失。",
  alternates: {
    canonical: "/zh/roadmap",
    languages: { "en-US": "/roadmap" },
  },
};

export default function ZhRoadmapPage() {
  return (
    <main className="min-h-screen">
      <ZhTranslationNotice />
      <section className="max-w-3xl mx-auto px-6 py-16">
        <Link href="/zh" className="text-teal-700 text-sm">← 返回首頁</Link>
        <h1 className="text-4xl font-bold mt-4">路線圖</h1>
        <p className="text-zinc-500 mt-2">
          公開路線圖。每個項目可在 GitHub Issues 上追蹤。
        </p>

        <h2 className="text-2xl font-semibold mt-10">2026 Q1 — 試點啟動</h2>
        <ul className="list-disc pl-6 mt-3 text-zinc-600 dark:text-zinc-300 space-y-1">
          <li>3 個城市的 B2G 試點 (阿納帕、索契、巴統)</li>
          <li>10 堂 EE 課程的中文翻譯校對</li>
          <li>論文投稿至 arXiv</li>
        </ul>

        <h2 className="text-2xl font-semibold mt-10">2026 Q2 — 模型擴展</h2>
        <ul className="list-disc pl-6 mt-3 text-zinc-600 dark:text-zinc-300 space-y-1">
          <li>地中海支援</li>
          <li>Stokes 漂流項 (Open-Meteo Marine API 已接入)</li>
          <li>河流源項加入 PINN</li>
        </ul>

        <h2 className="text-2xl font-semibold mt-10">2026 Q3 — 教育擴展</h2>
        <ul className="list-disc pl-6 mt-3 text-zinc-600 dark:text-zinc-300 space-y-1">
          <li>10 + 10 堂進階 EE 課程</li>
          <li>學校儀表板 (老師可以追蹤班級的環境素養進度)</li>
        </ul>

        <h2 className="text-2xl font-semibold mt-10">已知缺失</h2>
        <ul className="list-disc pl-6 mt-3 text-zinc-600 dark:text-zinc-300 space-y-1">
          <li>沒有垂直沉降模型 (僅深度積分)</li>
          <li>河流源項仍為近似</li>
          <li>真實衛星資料整合仍在測試</li>
          <li>中文 EE 課程需要母語者校對</li>
        </ul>

        <p className="mt-10 text-sm text-zinc-500">
          想協助嗎?寫信至{" "}
          <a href="mailto:scaleblinkk@vk.com" className="underline">scaleblinkk@vk.com</a>。
        </p>
      </section>
    </main>
  );
}
