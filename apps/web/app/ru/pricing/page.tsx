import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Цены — TideGuard AI",
  description:
    "Тарифы API, B2G-планы для муниципалитетов и портов, Adopt-a-Beach. Прозрачные цены, открытая лицензия.",
  alternates: {
    canonical: "/ru/pricing",
    languages: { "en-US": "/pricing", "zh-TW": "/zh/pricing" },
  },
};

const TIERS = [
  {
    slug: "free",
    name: "Free",
    price: "$0",
    period: "месяц",
    blurb: "Доступ для хобби и исследований — с атрибуцией.",
    features: [
      "1 000 запросов / мес",
      "10 rps мягкий лимит",
      "Прогноз PINN (7 дней)",
      "Гражданские репорты + уборки",
      "Публичные виджеты с атрибуцией",
    ],
    cta: "Получить ключ",
    highlight: false,
  },
  {
    slug: "pro",
    name: "Pro",
    price: "$49",
    period: "месяц",
    blurb: "Для стартапов, погодных приложений и небольших НКО.",
    features: [
      "100 000 запросов / мес",
      "60 rps мягкий лимит",
      "Исторический архив: 30 дней",
      "Горизонт прогноза: 14 дней",
      "Можно убрать атрибуцию",
      "Email-поддержка",
    ],
    cta: "Начать Pro",
    highlight: true,
  },
  {
    slug: "business",
    name: "Business",
    price: "$299",
    period: "месяц",
    blurb: "OGC WMS/WCS тайлы, год архива, 5 мест.",
    features: [
      "1 000 000 запросов / мес",
      "200 rps мягкий лимит",
      "OGC WMS / WCS эндпоинты",
      "Исторический архив: 365 дней",
      "PDF и CSV экспорт",
      "Приоритетная email-поддержка",
    ],
    cta: "Связаться с продажами",
    highlight: false,
  },
  {
    slug: "enterprise",
    name: "Enterprise",
    price: "По запросу",
    period: "год",
    blurb: "SLA, выделенный VPC, кастомные регионы.",
    features: [
      "Безлимит (fair-use)",
      "Кастомный SLA (99.9% / 99.95%)",
      "Приватные регионы / on-prem",
      "Single-tenant развёртывание",
      "Выделенный support-инженер",
    ],
    cta: "Связаться",
    highlight: false,
  },
];

const B2G_TIERS = [
  {
    slug: "b2g_basic",
    name: "B2G Basic",
    price: "$1 200",
    period: "месяц",
    features: ["1 регион", "Еженедельный PDF-отчёт", "Email-алерты", "Прогнозный дашборд"],
  },
  {
    slug: "b2g_pro",
    name: "B2G Pro",
    price: "$3 500",
    period: "месяц",
    features: ["3 региона", "VRP-маршрутизация уборок", "Telegram-алерты", "Доступ к API", "GeoJSON-экспорт"],
  },
  {
    slug: "b2g_enterprise",
    name: "B2G Enterprise",
    price: "от $8 000",
    period: "месяц",
    features: ["Безлимит регионов", "Несколько мест", "Кастомные интеграции", "Горячая линия 24×7", "Очное обучение"],
  },
];

const ADOPT_TIERS = [
  { slug: "adopt_individual", name: "Индивидуально", price: "$10", period: "месяц", note: "1 сегмент берега, имя на публичной карте" },
  { slug: "adopt_school", name: "Школа", price: "$25", period: "месяц", note: "5 сегментов, групповой дашборд" },
  { slug: "adopt_business", name: "Бизнес", price: "$200", period: "месяц", note: "10 сегментов, логотип спонсора, CSR-PDF" },
];

export default function RuPricingPage() {
  return (
    <main className="max-w-6xl mx-auto px-6 py-16">
      <header className="text-center mb-12">
        <h1 className="text-4xl font-bold">Цены, которые масштабируются с impact-эффектом</h1>
        <p className="text-zinc-500 mt-2 max-w-2xl mx-auto">
          Цены этапа soft-launch. На каждом платном тарифе — детерминистский
          биллинг, идемпотентность вебхуков и право удалить свои данные в один клик.
        </p>
      </header>

      <h2 className="text-xl font-semibold mb-4">Премиальные API-тарифы</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
        {TIERS.map((t) => (
          <div
            key={t.slug}
            className={`rounded-2xl border p-6 ${t.highlight ? "border-teal-600 shadow-lg shadow-teal-100" : "border-zinc-200"}`}
          >
            <div className="text-xs uppercase tracking-widest text-zinc-400">{t.name}</div>
            <div className="text-3xl font-bold mt-2">
              {t.price}
              <span className="text-base text-zinc-500"> / {t.period}</span>
            </div>
            <p className="text-sm text-zinc-500 mt-2">{t.blurb}</p>
            <ul className="text-sm mt-4 space-y-1">
              {t.features.map((f) => (
                <li key={f}>· {f}</li>
              ))}
            </ul>
            <Link
              href={`/billing/checkout?tier=${t.slug}`}
              className={`block text-center mt-5 rounded-md px-4 py-2 text-sm font-medium ${t.highlight ? "bg-teal-600 text-white hover:bg-teal-700" : "bg-zinc-100 hover:bg-zinc-200"}`}
            >
              {t.cta}
            </Link>
          </div>
        ))}
      </div>

      <h2 className="text-xl font-semibold mb-4">B2G — муниципалитеты и портовые администрации</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12">
        {B2G_TIERS.map((t) => (
          <div key={t.slug} className="rounded-2xl border border-zinc-200 p-6">
            <div className="text-xs uppercase tracking-widest text-zinc-400">{t.name}</div>
            <div className="text-2xl font-bold mt-2">
              {t.price}
              <span className="text-sm text-zinc-500"> / {t.period}</span>
            </div>
            <ul className="text-sm mt-4 space-y-1">
              {t.features.map((f) => (
                <li key={f}>· {f}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <h2 className="text-xl font-semibold mb-4">Adopt-a-Beach</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {ADOPT_TIERS.map((t) => (
          <div key={t.slug} className="rounded-2xl border border-zinc-200 p-6">
            <div className="text-xs uppercase tracking-widest text-zinc-400">{t.name}</div>
            <div className="text-2xl font-bold mt-2">
              {t.price}
              <span className="text-sm text-zinc-500"> / {t.period}</span>
            </div>
            <p className="text-sm text-zinc-500 mt-2">{t.note}</p>
            <Link
              href="/adopt-a-beach"
              className="block text-center mt-5 rounded-md bg-teal-600 text-white px-4 py-2 text-sm font-medium hover:bg-teal-700"
            >
              Усыновить берег
            </Link>
          </div>
        ))}
      </div>

      <section id="economics" className="mt-16 pt-14 border-t border-zinc-200 dark:border-zinc-800">
        <header className="text-center mb-8">
          <p className="uppercase tracking-widest text-xs text-teal-700 mb-2">Устойчивость</p>
          <h2 className="text-3xl font-bold">Экономика при масштабировании</h2>
          <p className="text-sm text-zinc-500 mt-2 max-w-2xl mx-auto">
            Юнит-экономика Year-1 (проекция). Публичный прогноз и 10 уроков
            остаются бесплатными по лицензии — потоки ниже их финансируют.
            Полные допущения в <code>docs/MONETIZATION.md</code>.
          </p>
        </header>
        <div className="overflow-x-auto rounded-2xl border border-zinc-200 dark:border-zinc-800">
          <table className="w-full text-sm">
            <thead className="bg-sand-50 dark:bg-zinc-900/60 text-left">
              <tr>
                <th className="px-4 py-3">Поток</th>
                <th className="px-4 py-3">Цена</th>
                <th className="px-4 py-3 text-right">Цель Year-1</th>
                <th className="px-4 py-3 text-right">Прогноз выручки</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
              <tr><td className="px-4 py-3">B2G муниципалитеты</td><td className="px-4 py-3">€6 000 / город / год</td><td className="px-4 py-3 text-right">4 города</td><td className="px-4 py-3 text-right">€24 000</td></tr>
              <tr><td className="px-4 py-3">Corporate ESG-отчёт</td><td className="px-4 py-3">€18 000 / отчёт</td><td className="px-4 py-3 text-right">6 отчётов</td><td className="px-4 py-3 text-right">€108 000</td></tr>
              <tr><td className="px-4 py-3">Лицензия данных для НКО</td><td className="px-4 py-3">€1 200 / год</td><td className="px-4 py-3 text-right">8 НКО</td><td className="px-4 py-3 text-right">€9 600</td></tr>
              <tr><td className="px-4 py-3">Образовательная лицензия</td><td className="px-4 py-3">€3 / ученик / год</td><td className="px-4 py-3 text-right">1 200 учеников</td><td className="px-4 py-3 text-right">€3 600</td></tr>
              <tr><td className="px-4 py-3">Гранты и спонсорство</td><td className="px-4 py-3">разово</td><td className="px-4 py-3 text-right">—</td><td className="px-4 py-3 text-right">€120 000</td></tr>
              <tr className="bg-teal-50/40 dark:bg-teal-950/30 font-semibold">
                <td className="px-4 py-3">Итого Year-1 (прогноз)</td>
                <td className="px-4 py-3"></td>
                <td className="px-4 py-3 text-right"></td>
                <td className="px-4 py-3 text-right text-teal-700">€265 200</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div className="grid md:grid-cols-3 gap-4 mt-8">
          <Stat label="Валовая маржа (B2G)" value="77%" note="В основном софт + минимум услуг" />
          <Stat label="CAC payback" value="≈ 18 мес." note="Mid-funnel B2G-обращение → подписанный пилот" />
          <Stat label="LTV / CAC" value="> 3×" note="Допущение об устойчивом продлении, консервативно" />
        </div>
        <p className="text-xs text-zinc-500 mt-6 text-center max-w-2xl mx-auto">
          Эти числа — <strong>прогноз</strong>, не факт. TideGuard сегодня
          до-доходный. Любую публичную проекцию мы помечаем как таковую и
          обновляем её ежеквартально в открытом репозитории.
        </p>
      </section>

      <p className="mt-12 text-center text-xs text-zinc-500">
        Цены в USD · Годовой план экономит 17 % · НДС где положено ·{" "}
        <Link href="/docs/billing" className="underline">FAQ по биллингу</Link>
      </p>
    </main>
  );
}

function Stat({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5">
      <div className="text-xs uppercase tracking-widest text-zinc-500">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
      <div className="text-sm text-zinc-500 mt-2">{note}</div>
    </div>
  );
}
