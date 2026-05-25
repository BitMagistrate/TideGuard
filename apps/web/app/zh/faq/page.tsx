import Link from "next/link";
import type { Metadata } from "next";
import ZhTranslationNotice from "../../../components/Lang/ZhTranslationNotice";

export const metadata: Metadata = {
  title: "常見問題 — TideGuard AI",
  description: "關於模型、資料、商業模式、安全性與道德的常見問題。",
  alternates: {
    canonical: "/zh/faq",
    languages: { "en-US": "/faq" },
  },
};

const QA: Array<{ q: string; a: React.ReactNode }> = [
  {
    q: "誰建構了 TideGuard?",
    a: (
      <>
        17 歲十年級的 Vladimir Ermolenko,就讀於西伯利亞克拉斯諾亞爾斯克第 13
        「Akadem」中學,以 AI 編碼副駕駛協助,3 個月內完成。請見{" "}
        <Link href="/zh/about" className="underline">創辦人故事</Link>。
      </>
    ),
  },
  {
    q: "為什麼選擇黑海?",
    a: "黑海是封閉的海盆,洋流相對良好刻劃,並且漂浮塑膠的攔截潛力很高。一旦在黑海驗證,模型結構可以擴展到其他海域。",
  },
  {
    q: "PINN 與一般神經網路有何不同?",
    a: "PINN 在訓練損失中同時包含資料項與偏微分方程殘差項。換言之,網路不僅要符合資料,還要遵守物理。這提高了在資料稀疏區的外推能力。",
  },
  {
    q: "你們的模型確實比 persistence 好嗎?",
    a: "是的:Bootstrap 95% CI 嚴格為負,Diebold–Mariano p < 3 × 10⁻¹¹²。詳見研究頁。",
  },
  {
    q: "免費方案會變成付費嗎?",
    a: "不會。現有的免費功能 (公開地圖、課程、公民通報) 永遠免費。我們把付費 B2G 儀表板與企業 API 作為平台的資金來源。",
  },
  {
    q: "你們收集個人資料嗎?",
    a: "公民通報可以匿名提交。我們不出售或分享個人資料。詳見隱私政策。",
  },
  {
    q: "我可以幫忙嗎?",
    a: (
      <>
        絕對歡迎。GitHub PR 開放給所有人;教育素材的翻譯尤其需要 (中文翻譯需要校對者!)
        請寄信至 <a href="mailto:scaleblinkk@vk.com" className="underline">scaleblinkk@vk.com</a>。
      </>
    ),
  },
];

export default function ZhFaqPage() {
  return (
    <main className="min-h-screen">
      <ZhTranslationNotice />
      <section className="max-w-3xl mx-auto px-6 py-16">
        <Link href="/zh" className="text-teal-700 text-sm">← 返回首頁</Link>
        <h1 className="text-4xl font-bold mt-4">常見問題</h1>
        <p className="text-zinc-500 mt-2">
          看不到您的問題嗎?寫信給{" "}
          <a href="mailto:scaleblinkk@vk.com" className="underline">scaleblinkk@vk.com</a>。
        </p>
        <div className="mt-10 space-y-6">
          {QA.map(({ q, a }) => (
            <div key={q} className="rounded-2xl border border-zinc-200 dark:border-zinc-800 p-6">
              <h2 className="text-lg font-semibold">{q}</h2>
              <div className="text-zinc-600 dark:text-zinc-300 mt-2">{a}</div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
