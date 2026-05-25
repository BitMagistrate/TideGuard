import Link from "next/link";
import type { Metadata } from "next";
import ZhTranslationNotice from "../../../components/Lang/ZhTranslationNotice";

export const metadata: Metadata = {
  title: "夥伴 — 學校、淨灘組織、城市",
  description: "TideGuard 的潛在試點夥伴與正在進行的合作。",
  alternates: {
    canonical: "/zh/partners",
    languages: { "en-US": "/partners" },
  },
};

export default function ZhPartnersPage() {
  return (
    <main className="min-h-screen">
      <ZhTranslationNotice />
      <section className="bg-gradient-to-br from-teal-700 to-ocean-600 text-white">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <p className="uppercase tracking-widest text-sand-100 text-xs mb-3">夥伴</p>
          <h1 className="text-4xl md:text-5xl font-bold">與我們一起預測,而非清掃。</h1>
          <p className="text-lg text-sand-50 mt-6 max-w-3xl">
            TideGuard 為三類夥伴而生:學校 (使用 EE 課程)、淨灘組織者 (使用預報計畫行動)
            與城市 (使用 B2G 儀表板規劃預算與路線)。
          </p>
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-6 py-16 grid md:grid-cols-3 gap-6">
        <Card title="學校" body="10 堂中文 EE 課程符合中學課綱。免費,CC-BY-4.0。" cta="瀏覽課程" href="/zh/learn" />
        <Card title="淨灘組織" body="14 天預報、清潔路線、社群儀表板。免費。" cta="開啟地圖" href="/map" />
        <Card title="城市與市政府" body="完整 B2G 儀表板、API、KPI 匯出、SLA 試點。" cta="申請試點" href="mailto:scaleblinkk@vk.com" />
      </section>

      <section className="bg-sand-50 dark:bg-zinc-900/40 py-16">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-6">正在進行的試點</h2>
          <ul className="space-y-3 text-sm">
            <li>• <strong>阿納帕</strong> (申請中,2026 Q1) —{" "}
              <Link href="/zh/b2g/anapa" className="underline">案例研究</Link></li>
            <li>• <strong>索契</strong> (探索性對話中)</li>
            <li>• <strong>巴統</strong> (探索性對話中)</li>
          </ul>
          <p className="text-xs text-zinc-500 mt-6">
            想成為早期夥伴?{" "}
            <a href="mailto:scaleblinkk@vk.com" className="underline">scaleblinkk@vk.com</a>。
          </p>
        </div>
      </section>
    </main>
  );
}

function Card({ title, body, cta, href }: { title: string; body: string; cta: string; href: string }) {
  return (
    <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 p-6 bg-white dark:bg-zinc-900">
      <h3 className="text-lg font-bold">{title}</h3>
      <p className="text-sm text-zinc-600 dark:text-zinc-300 mt-2">{body}</p>
      <Link href={href} className="inline-block mt-4 text-teal-700 underline text-sm">
        {cta} →
      </Link>
    </div>
  );
}
