import Link from "next/link";
import ZhTranslationNotice from "../../../components/Lang/ZhTranslationNotice";

export const metadata = {
  title: "TideGuard 運作原理 — 物理資訊神經網路",
  description:
    "TideGuard AI 背後的 PINN 模型非技術性介紹:物理、資料、基線與不確定性。",
  alternates: {
    canonical: "/zh/method",
    languages: { "en-US": "/method", "ru-RU": "/method" },
  },
};

export default function ZhMethodPage() {
  return (
    <main className="min-h-screen">
      <ZhTranslationNotice />
      <div className="max-w-3xl mx-auto px-6 py-12 prose dark:prose-invert">
        <Link href="/zh" className="text-teal-700 text-sm no-underline">← 返回首頁</Link>
        <h1>TideGuard 運作原理</h1>

        <div className="not-prose my-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-sand-50 dark:bg-zinc-900/60 text-left">
              <tr>
                <th className="px-4 py-3">模型</th>
                <th className="px-4 py-3 text-right">RMSE ↓</th>
                <th className="px-4 py-3 text-right">NSE ↑</th>
                <th className="px-4 py-3 text-right">相較 persistence</th>
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
                <td className="px-4 py-3">Persistence (基線)</td>
                <td className="px-4 py-3 text-right">0.1006</td>
                <td className="px-4 py-3 text-right">0.898</td>
                <td className="px-4 py-3 text-right text-zinc-500">baseline</td>
              </tr>
            </tbody>
          </table>
          <p className="text-xs text-zinc-500 px-4 py-3 border-t border-zinc-200 dark:border-zinc-800">
            Diebold–Mariano 與 persistence 對比顯著性:<code>p &lt; 3 × 10⁻¹¹²</code>。
            合成黑海問題,5 種子集成,14 天時程。OSF 預先註冊。完整表格與 bootstrap CI 見
            <Link href="/zh/research">/zh/research</Link>。
          </p>
        </div>

        <p>
          TideGuard 的預報來自 <strong>物理資訊神經網路 (PINN)</strong>。此方法
          由 <a href="https://www.sciencedirect.com/science/article/pii/S0021999118307125" target="_blank" rel="noopener">
          Raissi、Perdikaris 與 Karniadakis (2019)</a> 提出,結合神經網路的彈性
          與我們對系統的物理定律已知。網路不僅從資料學習,也必須滿足偏微分方程。
        </p>

        <h2>1. 物理</h2>
        <p>
          表層漂浮垃圾被洋流帶動,被風推動,並透過擱淺緩慢移除。我們求解的
          二維對流-擴散方程式為:
        </p>
        <pre>
          ∂C/∂t + ∇·((u_ocean + α·u_wind) · C) − ∇·(K · ∇C) + λ · C = S(x, y, t)
        </pre>
        <ul>
          <li><strong>C(x, y, t)</strong> — 表層垃圾濃度 (歸一化至 0..1)</li>
          <li><strong>u_ocean</strong> — 來自 Copernicus Marine Service 的表層洋流</li>
          <li><strong>u_wind</strong> — 來自 ECMWF ERA5 的 10 公尺風場</li>
          <li><strong>α, K, λ</strong> — 風漂效應、擴散、擱淺係數,皆<em>從資料學習</em>而非預設</li>
          <li><strong>S(x, y, t)</strong> — 源項 (例如河流);在合成基準中為零</li>
        </ul>

        <h2>2. 模型</h2>
        <p>
          一個六層 MLP,每層 128 隱藏單元,將 (x, y, t) → C。三個物理參數以
          可訓練純量的指數形式存在 (確保為正)。程式碼:
          <code>apps/ml/src/tideguard_ml/pinn.py</code>。
        </p>

        <h2>3. 損失函數</h2>
        <p>
          我們並行訓練四個損失項:資料項 (匹配觀測值)、PDE 殘差項 (物理)、
          初始條件項與邊界條件項。PyTorch 透過自動微分計算空間與時間導數。
        </p>

        <h2>4. 基線</h2>
        <ul>
          <li><strong>Persistence</strong>:明天與今天相同。若無法擊敗它,就不該部署。</li>
          <li><strong>拉格朗日粒子追蹤</strong>:相同物理的解析實作。
            程式碼於 <code>apps/ml/src/tideguard_ml/baselines/lagrangian.py</code>。</li>
        </ul>
        <p>
          在合成測試問題上,PINN 比 persistence RMSE 改善約 28%,比拉格朗日
          基線改善約 12% —— 完整表格見 <code>docs/research_paper.md</code>。
        </p>

        <h2>5. 不確定性與校準</h2>
        <p>
          我們訓練五個獨立種子並回報每像素標準差。地圖同時展示集成平均值
          與離散度,讓淨灘組織者知道模型在哪裡有信心、在哪裡只是猜測。
        </p>
        <p>
          此外我們計算 <strong>期望校準誤差 (ECE)</strong>,並在 ECE &gt; 0.05
          時套用 <strong>溫度縮放</strong> (Guo et al. 2017)。程式碼:
          <code>apps/ml/src/tideguard_ml/eval/calibration.py</code>。
        </p>

        <h2>6. 誠實的告解</h2>
        <ul>
          <li>僅深度積分,不建模垂直沉降。</li>
          <li>源項為近似;河流是主要待辦項目。</li>
          <li>Stokes 漂流在路線圖上 (Open-Meteo Marine API 已接入)。</li>
          <li>Model card (<code>docs/model_card.md</code>) 列出已知偏差。</li>
        </ul>

        <h2>7. 重現</h2>
        <pre>
          {`git clone https://github.com/BitMagistrate/TideGuard
cd TideGuard/apps/ml
uv venv && uv pip install -e ".[dev]"
uv run python -m tideguard_ml.train --synthetic --epochs 5000
uv run python -m tideguard_ml.baselines.benchmark --seeds 5`}
        </pre>
        <p className="text-sm text-zinc-500">
          開啟程式碼:
          <a href="https://github.com/BitMagistrate/TideGuard/tree/main/apps/ml">
            GitHub 上的 apps/ml
          </a>
          。
        </p>
      </div>
    </main>
  );
}
