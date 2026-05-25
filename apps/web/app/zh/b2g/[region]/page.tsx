"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import ZhTranslationNotice from "../../../../components/Lang/ZhTranslationNotice";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const DEMO_MODE = (process.env.NEXT_PUBLIC_DEMO_MODE ?? "1") !== "0";

type Summary = {
  region: string;
  max_p_exceed: number;
  kg_predicted: number;
  reports_last_7d: number;
  volunteers_last_7d: number;
  hotspot_count: number;
};

const DEMO_FALLBACK: Record<string, Summary> = {
  anapa: {
    region: "anapa",
    max_p_exceed: 0.84,
    kg_predicted: 5730,
    reports_last_7d: 47,
    volunteers_last_7d: 23,
    hotspot_count: 108,
  },
  sochi: {
    region: "sochi",
    max_p_exceed: 0.71,
    kg_predicted: 4210,
    reports_last_7d: 32,
    volunteers_last_7d: 18,
    hotspot_count: 86,
  },
};

const REGION_LABELS: Record<string, string> = {
  anapa: "阿納帕",
  sochi: "索契",
};

export default function ZhB2GRegionPage({ params }: { params: { region: string } }) {
  const { region } = params;
  const [s, setS] = useState<Summary | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const label = REGION_LABELS[region] || region;

  useEffect(() => {
    let alive = true;
    fetch(`${API}/b2g/dashboard/regions/${region}/summary`)
      .then((r) => (r.ok ? r.json() : null))
      .then((json: Summary | null) => {
        if (!alive) return;
        if (json && (json.kg_predicted > 0 || json.hotspot_count > 0 || json.max_p_exceed > 0)) {
          setS(json);
        } else if (DEMO_MODE && DEMO_FALLBACK[region]) {
          setS(DEMO_FALLBACK[region]);
        } else {
          setS(json);
        }
        setLoaded(true);
      })
      .catch(() => {
        if (!alive) return;
        if (DEMO_MODE && DEMO_FALLBACK[region]) {
          setS(DEMO_FALLBACK[region]);
        }
        setLoaded(true);
      });
    return () => {
      alive = false;
    };
  }, [region]);

  async function downloadPdf() {
    setBusy("pdf");
    try {
      const r = await fetch(`${API}/b2g/dashboard/regions/${region}/report.pdf`, {
        method: "POST",
      });
      if (!r.ok) {
        alert("PDF 生成失敗。Demo 模式需要 API 在執行中。");
        return;
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${region}-weekly-report.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="min-h-screen">
      <ZhTranslationNotice />
      <div className="max-w-5xl mx-auto px-6 py-12">
        <Link href="/zh" className="text-teal-700 text-sm">← 返回首頁</Link>
        <h1 className="text-3xl font-bold mt-2">{label}</h1>
        {DEMO_MODE && (
          <p className="mt-2 text-xs text-zinc-500">
            Demo 模式 —— KPI 反映該區域的合成預報種子。下方 ROI 計算器使用即時輸入。
          </p>
        )}
        {!loaded && <p className="mt-4 text-zinc-400">載入中…</p>}
        {loaded && !s && (
          <p className="mt-4 text-zinc-500">
            該區域尚無摘要。API 可能仍在初始化。請稍後再試。
          </p>
        )}
        {s && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
              <Kpi label="最大 p_exceed" value={`${(s.max_p_exceed * 100).toFixed(0)}%`} />
              <Kpi label="預測公斤數" value={s.kg_predicted.toFixed(0)} />
              <Kpi label="7 天內通報" value={String(s.reports_last_7d)} />
              <Kpi label="熱點數" value={String(s.hotspot_count)} />
            </div>
            <div className="mt-8 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={downloadPdf}
                disabled={busy === "pdf"}
                className="px-4 py-2 rounded-md bg-teal-600 text-white text-sm hover:bg-teal-700 disabled:opacity-50"
              >
                {busy === "pdf" ? "生成中…" : "下載週報 PDF"}
              </button>
              <a
                href={`${API}/b2g/dashboard/regions/${region}/export.geojson`}
                className="px-4 py-2 rounded-md bg-zinc-100 hover:bg-zinc-200 text-sm"
              >
                匯出 GeoJSON
              </a>
              <a
                href={`${API}/b2g/dashboard/regions/${region}/export.xlsx`}
                className="px-4 py-2 rounded-md bg-zinc-100 hover:bg-zinc-200 text-sm"
              >
                匯出 XLSX
              </a>
            </div>
          </>
        )}

        <ROISection regionLabel={label} />
        <CaseStudy region={region} label={label} />
      </div>
    </main>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="border rounded-xl p-4">
      <div className="text-xs uppercase text-zinc-400">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
    </div>
  );
}

function ROISection({ regionLabel }: { regionLabel: string }) {
  const [coastKm, setCoastKm] = useState(50);
  const [annualCostPerKm, setAnnualCostPerKm] = useState(1200);
  const [tonsIntercepted, setTonsIntercepted] = useState(8);
  const [disposalSavedPerTon, setDisposalSavedPerTon] = useState(220);
  const [volunteerMultiplier, setVolunteerMultiplier] = useState(1.6);

  const result = useMemo(() => {
    const annualCost = coastKm * annualCostPerKm;
    const disposalSaved = tonsIntercepted * disposalSavedPerTon;
    const volunteerValue = annualCost * (volunteerMultiplier - 1);
    const grossValue = annualCost + disposalSaved + volunteerValue;
    const tideguardCost = 6000;
    const roiPct = ((grossValue - tideguardCost) / tideguardCost) * 100;
    const paybackMonths = (tideguardCost / Math.max(grossValue, 1)) * 12;
    return { annualCost, disposalSaved, volunteerValue, grossValue, tideguardCost, roiPct, paybackMonths };
  }, [coastKm, annualCostPerKm, tonsIntercepted, disposalSavedPerTon, volunteerMultiplier]);

  return (
    <section id="roi" className="mt-16 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-sand-50 dark:bg-zinc-900/40 p-6">
      <header className="mb-4">
        <p className="uppercase tracking-widest text-xs text-teal-700">市政府 ROI</p>
        <h2 className="text-2xl font-bold mt-1">
          TideGuard 在 {regionLabel} 會回本嗎?
        </h2>
        <p className="text-sm text-zinc-500 mt-1">
          即時計算器。拖動輸入以符合您的海岸線。預設值來自{" "}
          <code>docs/ROI_CALCULATOR.md</code> 中的阿納帕基準假設。
        </p>
      </header>
      <div className="grid md:grid-cols-2 gap-4">
        <NumInput label="海岸線長度 (公里)" value={coastKm} onChange={setCoastKm} min={1} max={500} step={1} />
        <NumInput label="年度清潔成本 (€ / 公里)" value={annualCostPerKm} onChange={setAnnualCostPerKm} min={100} max={10000} step={50} />
        <NumInput label="擱淺前攔截的塑膠 (噸 / 年)" value={tonsIntercepted} onChange={setTonsIntercepted} min={0} max={500} step={1} />
        <NumInput label="節省的處置成本 (€ / 噸)" value={disposalSavedPerTon} onChange={setDisposalSavedPerTon} min={0} max={2000} step={10} />
        <NumInput label="志工乘數 (×)" value={volunteerMultiplier} onChange={setVolunteerMultiplier} min={1} max={5} step={0.1} />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
        <ResultCard label="總價值" value={`€${Math.round(result.grossValue).toLocaleString("en-US")}`} />
        <ResultCard label="TideGuard B2G 訂閱" value={`€${result.tideguardCost.toLocaleString("en-US")}`} />
        <ResultCard label="預估 ROI" value={`${Math.round(result.roiPct).toLocaleString("en-US")}%`} highlight />
        <ResultCard
          label="回本時間"
          value={`${result.paybackMonths < 12 ? result.paybackMonths.toFixed(2) : Math.round(result.paybackMonths)} 個月`}
          highlight
        />
      </div>
      <p className="text-xs text-zinc-500 mt-4">
        計算方法:總價值 = 年度清潔成本展開 + 節省的處置成本 + 志工時數價值提升。
        訂閱假設:€6 000 / 城市 / 年 (見 <Link href="/zh/pricing" className="underline">/zh/pricing</Link>)。
        僅為預估 —— TideGuard 尚未營收,阿納帕試點預定於 2026 年夏季開始。
      </p>
    </section>
  );
}

function NumInput({
  label, value, onChange, min, max, step,
}: {
  label: string; value: number; onChange: (n: number) => void; min: number; max: number; step: number;
}) {
  return (
    <label className="block">
      <span className="text-xs uppercase tracking-widest text-zinc-500">{label}</span>
      <input
        type="number"
        inputMode="decimal"
        value={Number.isFinite(value) ? value : 0}
        onChange={(e) => onChange(Number(e.target.value))}
        min={min}
        max={max}
        step={step}
        className="mt-1 w-full rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-2 text-base"
      />
    </label>
  );
}

function ResultCard({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div
      className={`rounded-xl p-4 border ${
        highlight
          ? "border-teal-600 bg-teal-50 dark:bg-teal-950/40"
          : "border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900"
      }`}
    >
      <div className="text-xs uppercase tracking-widest text-zinc-500">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${highlight ? "text-teal-700 dark:text-teal-300" : ""}`}>
        {value}
      </div>
    </div>
  );
}

function CaseStudy({ region, label }: { region: string; label: string }) {
  return (
    <section className="mt-16 rounded-2xl border border-zinc-200 dark:border-zinc-800 p-6">
      <header className="mb-4">
        <p className="uppercase tracking-widest text-xs text-teal-700">案例研究 (預估)</p>
        <h2 className="text-2xl font-bold mt-1">
          若 {label} 於 2026 年夏季簽約
        </h2>
        <p className="text-sm text-zinc-500 mt-1">
          中央阿納帕基準情境,來自 <code>docs/IMPACT.md</code>。所有數字為預估 —— 試點尚未簽約。
        </p>
      </header>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Mini label="攔截塑膠" value="500 公斤" />
        <Mini label="參與志工" value="75 人" />
        <Mini label="避免處置成本" value="≈ €10 000" />
        <Mini label="補助資本 ROI" value="≈ 6×" />
      </div>
    </section>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 p-4">
      <div className="text-xs uppercase tracking-widest text-zinc-500">{label}</div>
      <div className="text-xl font-bold mt-1">{value}</div>
    </div>
  );
}
