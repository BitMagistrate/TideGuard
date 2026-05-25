import Link from "next/link";
import type { Metadata } from "next";
import ZhTranslationNotice from "../../../components/Lang/ZhTranslationNotice";

export const metadata: Metadata = {
  title: "定價 — 免費公開地圖 + 付費 B2G 儀表板",
  description:
    "免費地圖與 10 堂 EE 課程,永遠免費。付費的 B2G 儀表板資助開源平台。",
  alternates: {
    canonical: "/zh/pricing",
    languages: { "en-US": "/pricing" },
  },
};

export default function ZhPricingPage() {
  return (
    <main className="min-h-screen">
      <ZhTranslationNotice />
      <section className="bg-gradient-to-br from-teal-700 to-ocean-600 text-white">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <p className="uppercase tracking-widest text-sand-100 text-xs mb-3">定價</p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            預設開源。公眾免費,永遠。
          </h1>
          <p className="text-lg text-sand-50 mt-6 max-w-3xl">
            公開的 14 天預報地圖與 10 堂環境教育課程依授權永遠免費。
            B2G 儀表板與高吞吐量 API 是付費的 —— 它們資助開源平台。
          </p>
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-3 gap-6">
          <Tier
            name="社群"
            price="€0"
            tagline="個人、學校、研究者、新聞媒體"
            features={[
              "14 天黑海預報地圖",
              "10 堂 EE 課程 (英、俄、中)",
              "公民通報 + 排行榜",
              "GitHub Issue 支援",
              "速率限制:60 req/min",
            ]}
            cta="開啟地圖"
            href="/map"
          />
          <Tier
            name="B2G 試點"
            price="€18 000 / 年"
            tagline="單一城市或自治區"
            featured
            features={[
              "KPI 儀表板 (PDF / GeoJSON / XLSX 匯出)",
              "清潔路線優化",
              "電子郵件支援 (≤24h)",
              "60 天 SLA 試點",
              "速率限制:600 req/min",
            ]}
            cta="申請試點"
            href="mailto:scaleblinkk@vk.com"
          />
          <Tier
            name="B2G 區域"
            price="€72 000 / 年"
            tagline="3+ 城市或一整個邊疆區"
            features={[
              "多租戶儀表板",
              "依需求 API",
              "電子郵件 + 視訊支援",
              "12 個月年度合約",
              "速率限制:6 000 req/min",
            ]}
            cta="洽談"
            href="mailto:scaleblinkk@vk.com"
          />
        </div>
        <p className="text-xs text-zinc-500 mt-6">
          所有金額不含稅。免費方案永遠免費 —— 我們不會「升級」現有的免費功能成付費。
        </p>
      </section>

      <section id="economics" className="bg-sand-50 dark:bg-zinc-900/40 py-16">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold">經濟學</h2>
          <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">
            專案第一年的預估收入。所有數字基於已表態的試點與已申請的補助。
            完整模型於 <code>docs/business_model.md</code>。
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-8">
            <Stat label="預估首年收入" value="€270k" note="B2G + 補助混合" />
            <Stat label="3 個 B2G 試點" value="€54k" note="阿納帕、索契、巴統" />
            <Stat label="補助" value="€216k" note="UN Ocean Decade、Microsoft AI for Good 等" />
            <Stat label="CAC 回收" value="≈ 18 個月" note="從詢問到簽約" />
          </div>
        </div>
      </section>

      <section className="bg-teal-700 text-white py-14">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold mb-3">試點申請</h2>
          <p className="text-sand-100 mb-6">
            首批 3 個城市試點正在進行中。寫信給我們了解阿納帕、索契或您自己的城市。
          </p>
          <div className="flex flex-wrap gap-3 justify-center">
            <a href="mailto:scaleblinkk@vk.com" className="px-5 py-3 bg-white text-teal-700 font-semibold rounded-lg">
              scaleblinkk@vk.com
            </a>
            <Link href="/zh/b2g/anapa" className="px-5 py-3 border border-white/30 rounded-lg hover:bg-white/10">
              阿納帕案例研究
            </Link>
            <Link href="/zh" className="px-5 py-3 border border-white/30 rounded-lg hover:bg-white/10">
              ← 首頁
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}

function Tier({
  name,
  price,
  tagline,
  features,
  cta,
  href,
  featured = false,
}: {
  name: string;
  price: string;
  tagline: string;
  features: string[];
  cta: string;
  href: string;
  featured?: boolean;
}) {
  return (
    <div
      className={`rounded-2xl border p-6 flex flex-col ${
        featured
          ? "border-teal-500 bg-teal-50 dark:bg-teal-950/30"
          : "border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900"
      }`}
    >
      <h3 className="text-xl font-bold">{name}</h3>
      <p className="text-sm text-zinc-500">{tagline}</p>
      <div className="text-3xl font-bold mt-4">{price}</div>
      <ul className="mt-6 space-y-2 text-sm flex-1">
        {features.map((f) => (
          <li key={f}>• {f}</li>
        ))}
      </ul>
      <a
        href={href}
        className={`mt-6 px-4 py-2 rounded-lg text-center font-medium ${
          featured ? "bg-teal-700 text-white" : "border border-zinc-300 dark:border-zinc-700"
        }`}
      >
        {cta}
      </a>
    </div>
  );
}

function Stat({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="text-center p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
      <div className="text-2xl md:text-3xl font-bold text-teal-700">{value}</div>
      <div className="text-xs text-zinc-500 mt-1 uppercase tracking-wider">{label}</div>
      <div className="text-xs text-zinc-400 mt-1">{note}</div>
    </div>
  );
}
