import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Roadmap 2026–2029",
  description:
    "Поэтапный план масштабирования TideGuard AI: от пилота на Чёрном море в 2026 до глобального открытого прогноза в 30+ странах к 2029.",
  alternates: {
    canonical: "/ru/roadmap",
    languages: { "en-US": "/roadmap", "zh-TW": "/zh/roadmap" },
  },
};

type Phase = {
  year: string;
  geography: string;
  reports: string;
  kg: string;
  countries: string;
  notes: string;
  highlight?: boolean;
};

const PHASES: Phase[] = [
  {
    year: "2026",
    geography: "Чёрное море (РФ-побережье)",
    reports: "5 000",
    kg: "1 200",
    countries: "1",
    notes: "Якорный пилот в Анапе + 3 школы, OSF препрегистрированный запуск на реальных данных.",
    highlight: true,
  },
  {
    year: "2027",
    geography: "+ BG / RO / TR побережье",
    reports: "25 000",
    kg: "8 000",
    countries: "4",
    notes: "Трансграничные MoU, мультиязычные уроки (болгарский, румынский, турецкий), первые подписанные B2G-дашборды.",
  },
  {
    year: "2028",
    geography: "+ Средиземное море + ЮВА",
    reports: "100 000",
    kg: "40 000",
    countries: "12",
    notes: "Модуль Stokes drift + связка с речными источниками. Breakeven по B2G-подпискам.",
  },
  {
    year: "2029",
    geography: "Глобально",
    reports: "400 000",
    kg: "180 000",
    countries: "30+",
    notes: "Federated training между региональными партнёрами, мультиязычный Adopt-a-Beach.",
  },
];

export default function RuRoadmapPage() {
  return (
    <main className="min-h-screen">
      <section className="bg-gradient-to-br from-teal-700 to-ocean-600 text-white">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <p className="uppercase tracking-widest text-sand-100 text-xs mb-3">Roadmap</p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            От одного пляжа в Анапе до 30+ стран за 4 года.
          </h1>
          <p className="text-lg text-sand-50 mt-6 max-w-3xl">
            Мы публикуем план масштабирования открыто — включая точки отказа
            и бюджеты. North-star метрики написаны так, чтобы любой читатель
            мог спросить с нас в следующем году.
          </p>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="overflow-x-auto rounded-2xl border border-zinc-200 dark:border-zinc-800">
          <table className="w-full text-sm">
            <thead className="bg-sand-50 dark:bg-zinc-900/60 text-left">
              <tr>
                <th className="px-4 py-3">Год</th>
                <th className="px-4 py-3">География</th>
                <th className="px-4 py-3 text-right">Граждан. репорты / год</th>
                <th className="px-4 py-3 text-right">кг убрано / год</th>
                <th className="px-4 py-3 text-right">Стран</th>
                <th className="px-4 py-3">Веха</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
              {PHASES.map((p) => (
                <tr
                  key={p.year}
                  className={
                    p.highlight ? "bg-teal-50/40 dark:bg-teal-950/30 font-semibold" : ""
                  }
                >
                  <td className="px-4 py-3 whitespace-nowrap">{p.year}</td>
                  <td className="px-4 py-3">{p.geography}</td>
                  <td className="px-4 py-3 text-right">{p.reports}</td>
                  <td className="px-4 py-3 text-right">{p.kg}</td>
                  <td className="px-4 py-3 text-right">{p.countries}</td>
                  <td className="px-4 py-3 text-zinc-600 dark:text-zinc-400 font-normal">
                    {p.notes}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="grid md:grid-cols-3 gap-4 mt-10">
          <Card label="Бюджет Year 1" value="$1 624" note="Хостинг сверх free-tier + одна выездная поездка" />
          <Card label="Run-rate Year 2" value="$3 000 / мес" note="Два со-лида, платный хостинг, квота на спутниковые данные" />
          <Card label="Run-rate Year 4" value="$8–12k / мес" note="Federated-кластер обучения + региональные инженеры" />
        </div>
        <p className="text-sm text-zinc-500 mt-6">
          Подробный фазовый план и юнит-экономика:{" "}
          <code>docs/scaling_plan_2026_2029.md</code>. Risk register:{" "}
          <code>docs/risk_register.md</code>. North-star метрики ведём публично
          в <Link href="/leaderboard" className="underline">лидерборде</Link>.
        </p>
      </section>

      <section className="bg-sand-50 dark:bg-zinc-900/40 py-14">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-2xl font-bold">Breakeven и устойчивость</h2>
          <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">
            Публичный прогноз и уроки остаются бесплатными по лицензии.
            Премиальные API, B2G-дашборды и Adopt-a-Beach финансируют открытую
            платформу. Blended-выручка Year-1 прогнозируется на уровне €270k
            (B2G + гранты); см.{" "}
            <Link href="/ru/pricing#economics" className="underline">/ru/pricing</Link>.
            Breakeven по B2G-подпискам прогнозируется на <strong>2028</strong>.
          </p>
        </div>
      </section>
    </main>
  );
}

function Card({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5">
      <div className="text-xs uppercase tracking-widest text-zinc-500">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
      <div className="text-sm text-zinc-500 mt-2">{note}</div>
    </div>
  );
}
