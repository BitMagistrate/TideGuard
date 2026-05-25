import Link from "next/link";
import type { Metadata } from "next";
import ZhTranslationNotice from "../../components/Lang/ZhTranslationNotice";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const GITHUB = process.env.NEXT_PUBLIC_GITHUB_URL || "https://github.com/BitMagistrate/TideGuard";
const CONTACT_EMAIL = "scaleblinkk@vk.com";

export const metadata: Metadata = {
  title: "TideGuard AI — 海洋塑膠開源預報",
  description:
    "物理資訊神經網路 (PINN) 預測黑海漂浮塑膠垃圾。MIT 授權,OSF 預先註冊,由 17 歲十年級學生在 3 個月內以 AI 編碼副駕駛協助完成。",
  alternates: {
    canonical: "/zh",
    languages: { "en-US": "/", "ru-RU": "/ru" },
  },
};

type CleanupStats = { cleanups: number; kg_collected: number; participants: number };
type PublicKPI = { lessons_completed: number };

async function fetchCleanupStats(): Promise<CleanupStats | null> {
  try {
    const res = await fetch(`${API}/cleanups/stats`, { next: { revalidate: 60 } });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

async function fetchPublicKPI(): Promise<PublicKPI | null> {
  try {
    const res = await fetch(`${API}/admin/kpi_public`, { next: { revalidate: 60 } });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

function formatInt(n: number | undefined | null): string {
  if (n === undefined || n === null) return "—";
  return n.toLocaleString("zh-Hant");
}

export default async function ZhHomePage() {
  const [stats, kpi] = await Promise.all([fetchCleanupStats(), fetchPublicKPI()]);

  return (
    <main className="min-h-screen">
      <ZhTranslationNotice />

      {/* Hero */}
      <section className="relative bg-gradient-to-br from-teal-700 via-teal-600 to-ocean-600 text-white">
        <div className="max-w-6xl mx-auto px-6 py-24">
          <p className="uppercase tracking-widest text-sand-100 text-sm mb-4">
            為海洋而生的物理資訊 AI
          </p>
          <h1 className="text-5xl md:text-6xl font-bold leading-tight max-w-3xl">
            在塑膠垃圾抵達海岸之前,AI 已先一步預測。
          </h1>
          <p className="text-lg md:text-xl text-sand-50 max-w-2xl mt-6">
            TideGuard AI 結合 Sentinel 衛星影像、海洋洋流、ECMWF 風場再分析
            與公民通報,使用物理資訊神經網路 (PINN) 預測未來 14 天黑海漂浮
            垃圾的熱點,並將預測轉化為社群行動。
          </p>
          <div className="flex flex-wrap gap-3 mt-8">
            <Link href="/map" className="px-6 py-3 bg-white text-teal-700 font-semibold rounded-lg hover:bg-sand-50">
              開啟即時地圖
            </Link>
            <Link href="/zh/learn" className="px-6 py-3 border border-white/30 rounded-lg hover:bg-white/10">
              10 堂中文課程
            </Link>
            <Link href="/zh/method" className="px-6 py-3 border border-white/30 rounded-lg hover:bg-white/10">
              模型運作原理
            </Link>
            <a href={GITHUB} className="px-6 py-3 border border-white/30 rounded-lg hover:bg-white/10">
              開源儲存庫
            </a>
          </div>
        </div>
      </section>

      {/* Proof block */}
      <section className="bg-sand-50 dark:bg-zinc-900/40 py-16">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-10">
            <p className="uppercase tracking-widest text-xs text-teal-700 mb-2">證據</p>
            <h2 className="text-3xl font-bold">評審會詢問的數字</h2>
            <p className="text-sm text-zinc-500 mt-2 max-w-2xl mx-auto">
              所有四項主要數字皆由本儲存庫的開源程式計算,並記錄於{" "}
              <Link href="/zh/research" className="underline">/zh/research</Link>。
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <BigStat value="279×" label="每排放 1 單位 CO₂ 所避免的 CO₂ 量" href="/zh/research" />
            <BigStat value="304%" label="阿納帕試點 2.97 個月 ROI" href="/zh/b2g/anapa" />
            <BigStat value="p < 3×10⁻¹¹²" label="Diebold–Mariano 顯著性檢定" href="/zh/research" />
            <BigStat value="€270k" label="首年預估收入 (B2G + 補助)" href="/zh/pricing" />
          </div>
        </div>
      </section>

      {/* Founder card */}
      <section className="bg-teal-50 dark:bg-teal-950/30 py-16">
        <div className="max-w-4xl mx-auto px-6 flex flex-col md:flex-row gap-8 items-center">
          <div className="w-32 h-32 shrink-0 rounded-full bg-gradient-to-br from-teal-500 to-ocean-600 grid place-items-center text-white text-4xl font-bold">
            VE
          </div>
          <div>
            <div className="text-xs uppercase tracking-widest text-teal-700">創辦人</div>
            <h3 className="text-2xl font-bold mt-1">Vladimir Ermolenko, 17 歲,克拉斯諾亞爾斯克</h3>
            <p className="text-zinc-600 dark:text-zinc-300 mt-2">
              第十三「Akadem」中學十年級,西伯利亞克拉斯諾亞爾斯克。在{" "}
              <strong>3 個月內以 AI 編碼副駕駛協助</strong>建構 TideGuard ——
              每一項設計決策、基準測試與公開文案皆由創辦人親自審查與整合。
              徵求學術導師與 1–2 位同齡共同負責人。MIT 授權,無隱藏團隊。
            </p>
            <div className="mt-3 flex flex-wrap gap-3 text-sm">
              <Link href="/zh/about" className="text-teal-700 underline">閱讀完整創辦人故事 →</Link>
              <a href={`mailto:${CONTACT_EMAIL}`} className="text-zinc-500 underline">{CONTACT_EMAIL}</a>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-semibold">即時社群影響</h2>
          <p className="text-sm text-zinc-500 mt-1">
            以下數字為產品資料庫的實際計數,每分鐘更新。專案啟動前,我們誠實顯示零,
            而非編造的「1 240 公斤已收集」。
          </p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <Stat label="清潔行動次數" value={formatInt(stats?.cleanups ?? 0)} />
          <Stat label="收集公斤數" value={formatInt(Math.round(stats?.kg_collected ?? 0))} />
          <Stat label="志工人數" value={formatInt(stats?.participants ?? 0)} />
          <Stat label="完成課程數" value={formatInt(kpi?.lessons_completed ?? 0)} />
        </div>
      </section>

      {/* What inside */}
      <section className="bg-sand-50 dark:bg-zinc-900/40 py-16">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12">平台內容</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <Card title="1. 公開地圖 (免費)" body="黑海 14 天預報網頁地圖,含「超出閾值機率」P(exceed) 圖層。開源程式。" />
            <Card title="2. 環境教育模組 (免費)" body="10 堂關於海洋塑膠、海洋物理與公民科學的課程。英、俄、中文。對應俄羅斯 FGOS 課綱。" />
            <Card title="3. B2G 儀表板 (付費)" body="市政府 KPI 面板、PDF / GeoJSON / XLSX 匯出、清潔路線規劃。付費營收支撐免費地圖與課程。" />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="max-w-6xl mx-auto px-6 py-10 text-sm text-zinc-500">
        <div className="grid md:grid-cols-3 gap-6">
          <div>
            <div className="font-semibold text-zinc-700 dark:text-zinc-300 mb-2">TideGuard AI</div>
            <p>漂浮海洋垃圾開源預報。程式 MIT 授權,課程內容 CC-BY-4.0。</p>
          </div>
          <div>
            <div className="font-semibold text-zinc-700 dark:text-zinc-300 mb-2">導覽</div>
            <ul className="space-y-1">
              <li><Link href="/map" className="hover:text-teal-700">預報地圖</Link></li>
              <li><Link href="/zh/method" className="hover:text-teal-700">方法 (PINN)</Link></li>
              <li><Link href="/zh/research" className="hover:text-teal-700">科學基礎</Link></li>
              <li><Link href="/zh/about" className="hover:text-teal-700">關於作者</Link></li>
            </ul>
          </div>
          <div>
            <div className="font-semibold text-zinc-700 dark:text-zinc-300 mb-2">聯絡</div>
            <ul className="space-y-1">
              <li><a href={`mailto:${CONTACT_EMAIL}`} className="hover:text-teal-700">{CONTACT_EMAIL}</a></li>
              <li><a href={GITHUB} className="hover:text-teal-700">GitHub 儲存庫</a></li>
              <li><Link href="/" className="hover:text-teal-700">English version</Link></li>
              <li><Link href="/ru" className="hover:text-teal-700">Русская версия</Link></li>
            </ul>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-zinc-200 dark:border-zinc-800 text-center">
          © 2026 TideGuard AI · 程式 MIT 授權 · 內容 CC-BY-4.0
        </div>
      </footer>
    </main>
  );
}

function BigStat({ value, label, href }: { value: string; label: string; href: string }) {
  return (
    <Link
      href={href}
      className="block text-center p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 hover:border-teal-500 transition"
    >
      <div className="text-2xl md:text-3xl font-bold text-teal-700 dark:text-teal-400">{value}</div>
      <div className="text-xs text-zinc-500 mt-2 leading-snug">{label}</div>
    </Link>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
      <div className="text-3xl md:text-4xl font-bold text-teal-600">{value}</div>
      <div className="text-sm text-zinc-500 mt-2 uppercase tracking-wider">{label}</div>
    </div>
  );
}

function Card({ title, body }: { title: string; body: string }) {
  return (
    <div className="p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-sm text-zinc-600 dark:text-zinc-400">{body}</p>
    </div>
  );
}
