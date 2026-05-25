import Link from "next/link";
import type { Metadata } from "next";
import ZhTranslationNotice from "../../../components/Lang/ZhTranslationNotice";

export const metadata: Metadata = {
  title: "媒體 — 新聞素材 & 媒體聯絡人",
  description: "TideGuard AI 的媒體素材、引言與聯絡方式。",
  alternates: {
    canonical: "/zh/press",
    languages: { "en-US": "/press" },
  },
};

export default function ZhPressPage() {
  return (
    <main className="min-h-screen">
      <ZhTranslationNotice />
      <section className="max-w-3xl mx-auto px-6 py-16">
        <Link href="/zh" className="text-teal-700 text-sm">← 返回首頁</Link>
        <h1 className="text-4xl font-bold mt-4">媒體</h1>
        <p className="text-zinc-500 mt-2">
          媒體聯絡:{" "}
          <a href="mailto:scaleblinkk@vk.com" className="underline">scaleblinkk@vk.com</a>
        </p>

        <h2 className="text-2xl font-semibold mt-10">概要</h2>
        <p className="mt-3 text-zinc-600 dark:text-zinc-300">
          TideGuard AI 是用於預測黑海漂浮塑膠垃圾的開源平台。其物理資訊神經
          網路 (PINN) 在 14 天時程上,以統計顯著差異擊敗 persistence 與
          拉格朗日基線。由 17 歲十年級的西伯利亞學生 Vladimir Ermolenko 與
          AI 編碼副駕駛在 3 個月內建構。MIT 授權。
        </p>

        <h2 className="text-2xl font-semibold mt-10">媒體素材</h2>
        <ul className="mt-3 space-y-2 text-sm">
          <li>• 創辦人故事 (英文): <Link href="/about" className="underline">/about</Link></li>
          <li>• 創辦人故事 (中文): <Link href="/zh/about" className="underline">/zh/about</Link></li>
          <li>• 研究 & 基準: <Link href="/zh/research" className="underline">/zh/research</Link></li>
          <li>• 模型卡: <code>docs/model_card.md</code> (儲存庫)</li>
          <li>• 開源儲存庫: <a href="https://github.com/BitMagistrate/TideGuard" className="underline">GitHub</a></li>
        </ul>

        <h2 className="text-2xl font-semibold mt-10">引言</h2>
        <blockquote className="mt-3 italic border-l-4 border-teal-500 pl-4 text-zinc-700 dark:text-zinc-300">
          「我們可以在潮水<em>之前</em>到達海灘,而非之後。那就是擦地板與
          關水龍頭的差別。」 —— Vladimir Ermolenko,創辦人
        </blockquote>
      </section>
    </main>
  );
}
