import Link from "next/link";
import type { Metadata } from "next";
import ZhTranslationNotice from "../../../components/Lang/ZhTranslationNotice";

export const metadata: Metadata = {
  title: "研究 — 基準、預先註冊、可重現",
  description:
    "TideGuard AI 的開源研究頁面:PINN 與 persistence、拉格朗日基線對比、Diebold-Mariano 檢定、OSF 預先註冊、碳足跡與單命令重現。",
  alternates: {
    canonical: "/zh/research",
    languages: { "en-US": "/research" },
  },
};

const GITHUB = "https://github.com/BitMagistrate/TideGuard";

export default function ZhResearchPage() {
  return (
    <main className="min-h-screen">
      <ZhTranslationNotice />

      <section className="bg-gradient-to-br from-teal-700 to-ocean-600 text-white">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <p className="uppercase tracking-widest text-sand-100 text-xs mb-3">開放研究</p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            預先註冊。可重現。MIT 授權。
          </h1>
          <p className="text-lg text-sand-50 mt-6 max-w-3xl">
            本網站的每一項主張都是由本儲存庫開源程式碼計算出來的數字。
            成功標準在我們對真實資料執行模型<em>之前</em>就已註冊。您可以
            在自己的筆電上以約 10 分鐘重現主要基準。
          </p>
          <div className="flex flex-wrap gap-2 mt-8 text-xs">
            <Badge>MIT 授權</Badge>
            <Badge>OSF 預先註冊</Badge>
            <Badge>arXiv (投稿中)</Badge>
            <Badge>Zenodo DOI</Badge>
            <Badge>CC-BY-4.0 課程</Badge>
            <Badge>OpenSSF Best Practices</Badge>
          </div>
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold">1. 基準</h2>
        <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">
          我們以合成黑海測試問題對 PINN 與三個已發表基線比較。五個獨立訓練種子。
          14 天時程。主要數字:<strong>RMSE 0.0929, NSE 0.913</strong>。
        </p>
        <div className="overflow-x-auto mt-6 rounded-2xl border border-zinc-200 dark:border-zinc-800">
          <table className="w-full text-sm">
            <thead className="bg-sand-50 dark:bg-zinc-900/60">
              <tr className="text-left">
                <th className="px-4 py-3">模型</th>
                <th className="px-4 py-3 text-right">RMSE ↓</th>
                <th className="px-4 py-3 text-right">NSE ↑</th>
                <th className="px-4 py-3 text-right">Δ vs persistence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
              <tr className="bg-teal-50/40 dark:bg-teal-950/30 font-semibold">
                <td className="px-4 py-3">PINN (本專案)</td>
                <td className="px-4 py-3 text-right">0.0929</td>
                <td className="px-4 py-3 text-right">0.913</td>
                <td className="px-4 py-3 text-right text-teal-700">−7.6%</td>
              </tr>
              <tr>
                <td className="px-4 py-3">拉格朗日 (5000 粒子)</td>
                <td className="px-4 py-3 text-right">0.0972</td>
                <td className="px-4 py-3 text-right">0.904</td>
                <td className="px-4 py-3 text-right">−3.4%</td>
              </tr>
              <tr>
                <td className="px-4 py-3">Persistence</td>
                <td className="px-4 py-3 text-right">0.1006</td>
                <td className="px-4 py-3 text-right">0.898</td>
                <td className="px-4 py-3 text-right text-zinc-500">baseline</td>
              </tr>
              <tr>
                <td className="px-4 py-3">氣候態 (Climatology)</td>
                <td className="px-4 py-3 text-right">0.1234</td>
                <td className="px-4 py-3 text-right">0.847</td>
                <td className="px-4 py-3 text-right text-zinc-500">+22.7%</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-sm text-zinc-500 mt-3">
          Diebold–Mariano 檢定相較 persistence:<code>p &lt; 3 × 10⁻¹¹²</code>。
          RMSE 差異的 Bootstrap 95% CI 嚴格為負 —— 見下方預先註冊接受規則。
        </p>
      </section>

      <section className="bg-sand-50 dark:bg-zinc-900/40 py-16">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold">2. 預先註冊接受規則</h2>
          <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">
            我們在 OSF 上對成功規則做了預先註冊,<em>在</em>對真實資料執行模型<em>之前</em>。
            禁止選擇性報告。
          </p>
          <ul className="list-disc pl-6 mt-4 text-sm space-y-2">
            <li>主要指標:RMSE 相對 persistence 改善 (5 種子集成,14 天時程)。</li>
            <li>接受規則:RMSE 差異的 Bootstrap 95% CI 嚴格為負,且 Diebold–Mariano p &lt; 0.01。</li>
            <li>沒有「事後 cherry-picking」: 我們鎖定種子、超參數與測試集。</li>
          </ul>
        </div>
      </section>

      <section id="carbon" className="max-w-5xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold">3. 碳足跡</h2>
        <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">
          訓練 PINN 預估排放約 <strong>1.6 kg CO₂eq</strong> (codecarbon 量測,
          歐洲電網)。每次淨灘避免約 <strong>447 kg CO₂eq</strong> (依文獻引用)。
          <strong>淨效益比例:每排放 1 單位 CO₂ 可避免 279 單位</strong>。
        </p>
      </section>

      <section className="bg-sand-50 dark:bg-zinc-900/40 py-16">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold">4. 重現</h2>
          <pre className="bg-zinc-900 text-white p-4 rounded-lg overflow-x-auto text-sm mt-4">
            {`git clone https://github.com/BitMagistrate/TideGuard
cd TideGuard/apps/ml
uv venv && uv pip install -e ".[dev]"
uv run python -m tideguard_ml.train --synthetic --epochs 5000
uv run python -m tideguard_ml.baselines.benchmark --seeds 5`}
          </pre>
          <p className="text-sm text-zinc-500 mt-3">
            預計筆電上約 10 分鐘。完整論文於 <code>docs/research_paper.md</code>,
            模型卡於 <code>docs/model_card.md</code>。
          </p>
        </div>
      </section>

      <section className="bg-teal-700 text-white py-14">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold mb-3">完全開放科學。</h2>
          <p className="text-sand-100 mb-6">
            程式 MIT 授權,內容 CC-BY-4.0。我們鼓勵您 fork、修改、批評,並回報問題。
          </p>
          <div className="flex flex-wrap gap-3 justify-center">
            <a href={GITHUB} className="px-5 py-3 bg-white text-teal-700 font-semibold rounded-lg">
              GitHub
            </a>
            <Link href="/zh/method" className="px-5 py-3 border border-white/30 rounded-lg hover:bg-white/10">
              方法
            </Link>
            <Link href="/zh" className="px-5 py-3 border border-white/30 rounded-lg hover:bg-white/10">
              ← 返回首頁
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-white/30 bg-white/10 px-3 py-1 text-white">
      {children}
    </span>
  );
}
