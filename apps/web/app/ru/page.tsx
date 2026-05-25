import Link from "next/link";
import type { Metadata } from "next";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const GITHUB = process.env.NEXT_PUBLIC_GITHUB_URL || "https://github.com/BitMagistrate/TideGuard";
const CONTACT_EMAIL = "scaleblinkk@vk.com";

export const metadata: Metadata = {
  title: "TideGuard AI — открытый прогноз морского пластика",
  description:
    "Physics-Informed Neural Network прогнозирует плавающий пластик на Чёрном море за 48–72 часа до того, как он окажется на берегу. MIT-лицензия, OSF preregistration.",
  alternates: { canonical: "/ru", languages: { "en-US": "/", "zh-TW": "/zh" } },
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
  return n.toLocaleString("ru-RU");
}

export default async function RuHomePage() {
  const [stats, kpi] = await Promise.all([fetchCleanupStats(), fetchPublicKPI()]);

  return (
    <main className="min-h-screen">


      {/* Hero */}
      <section className="relative bg-gradient-to-br from-teal-700 via-teal-600 to-ocean-600 text-white">
        <div className="max-w-6xl mx-auto px-6 py-24">
          <p className="uppercase tracking-widest text-sand-100 text-sm mb-4">
            Physics-Informed AI для наших морей
          </p>
          <h1 className="text-5xl md:text-6xl font-bold leading-tight max-w-3xl">
            ИИ, который прогнозирует пластик до того, как он окажется на берегу.
          </h1>
          <p className="text-lg md:text-xl text-sand-50 max-w-2xl mt-6">
            TideGuard AI объединяет данные Sentinel, океанические течения,
            ветер ECMWF и гражданские репорты, чтобы прогнозировать «горячие
            точки» морского мусора на 14 дней вперёд — и превращает прогноз в
            действие сообщества.
          </p>
          <div className="flex flex-wrap gap-3 mt-8">
            <Link href="/map" className="px-6 py-3 bg-white text-teal-700 font-semibold rounded-lg hover:bg-sand-50">
              Открыть карту
            </Link>
            <Link href="/learn?lang=ru" className="px-6 py-3 border border-white/30 rounded-lg hover:bg-white/10">
              10 уроков на русском
            </Link>
            <Link href="/method" className="px-6 py-3 border border-white/30 rounded-lg hover:bg-white/10">
              Как работает модель
            </Link>
            <a href={GITHUB} className="px-6 py-3 border border-white/30 rounded-lg hover:bg-white/10">
              Открытый репозиторий
            </a>
          </div>
        </div>
      </section>

      {/* Proof block */}
      <section className="bg-sand-50 dark:bg-zinc-900/40 py-16">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-10">
            <p className="uppercase tracking-widest text-xs text-teal-700 mb-2">Доказательства</p>
            <h2 className="text-3xl font-bold">Цифры, которые попросит жюри</h2>
            <p className="text-sm text-zinc-500 mt-2 max-w-2xl mx-auto">
              Все четыре числа считаются из открытого кода в этом репозитории и
              задокументированы на <Link href="/research" className="underline">/research</Link>.
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <BigStat value="279×" label="предотвращённого CO₂ на 1 CO₂ потраченного" href="/research#carbon" />
            <BigStat value="304%" label="ROI пилота Анапы за 2.97 месяца" href="/b2g/anapa" />
            <BigStat value="p < 3×10⁻¹¹²" label="Diebold–Mariano против persistence" href="/research#benchmark" />
            <BigStat value="€270k" label="прогноз выручки за 1-й год (B2G + гранты)" href="/pricing#economics" />
          </div>
        </div>
      </section>

      {/* About author */}
      <section className="bg-teal-50 dark:bg-teal-950/30 py-16">
        <div className="max-w-4xl mx-auto px-6 flex flex-col md:flex-row gap-8 items-center">
          <div className="w-32 h-32 shrink-0 rounded-full bg-gradient-to-br from-teal-500 to-ocean-600 grid place-items-center text-white text-4xl font-bold">
            ВЕ
          </div>
          <div>
            <div className="text-xs uppercase tracking-widest text-teal-700">Автор</div>
            <h3 className="text-2xl font-bold mt-1">Владимир Ермоленко, 17 лет, Красноярск</h3>
            <p className="text-zinc-600 dark:text-zinc-300 mt-2">
              10 класс Гимназии №13 «Академ», Красноярск, Сибирь.
              Построил TideGuard за <strong>3 месяца с ИИ-копилотом</strong>{" "}
              — каждое проектное решение, бенчмарк и строка публичного текста
              на этом сайте проверены и интегрированы автором. MIT-лицензия,
              никакой скрытой команды.
            </p>
            <div className="mt-3 flex flex-wrap gap-3 text-sm">
              <Link href="/ru/about" className="text-teal-700 underline">Полная история основателя →</Link>
              <a href={`mailto:${CONTACT_EMAIL}`} className="text-zinc-500 underline">{CONTACT_EMAIL}</a>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-semibold">Реальные показатели платформы</h2>
          <p className="text-sm text-zinc-500 mt-1">
            Цифры ниже — это фактические счётчики из продакшен-БД. Пока проект на старте,
            мы честно показываем нули, а не выдуманные «1 240 кг собрано».
          </p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <Stat label="уборок" value={formatInt(stats?.cleanups ?? 0)} />
          <Stat label="кг собрано" value={formatInt(Math.round(stats?.kg_collected ?? 0))} />
          <Stat label="волонтёров" value={formatInt(stats?.participants ?? 0)} />
          <Stat label="уроков завершено" value={formatInt(kpi?.lessons_completed ?? 0)} />
        </div>
      </section>

      {/* What inside */}
      <section className="bg-sand-50 dark:bg-zinc-900/40 py-16">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12">Что внутри платформы</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <Card title="1. Публичная карта (бесплатно)" body="Веб-карта Чёрного моря, прогноз на 14 дней, слой «вероятность превышения порога» (P(exceed)). Открытый код." />
            <Card title="2. Образовательный модуль (бесплатно)" body="10 уроков по морскому пластику, физике океана и гражданской науке. Английский, русский, китайский. Привязка к ФГОС." />
            <Card title="3. B2G-дашборд (платно)" body="KPI-панель для муниципалитетов, экспорт PDF / GeoJSON / XLSX, маршрутизация уборок. Платный трек финансирует бесплатные карту и уроки." />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="max-w-6xl mx-auto px-6 py-10 text-sm text-zinc-500">
        <div className="grid md:grid-cols-3 gap-6">
          <div>
            <div className="font-semibold text-zinc-700 dark:text-zinc-300 mb-2">TideGuard AI</div>
            <p>Открытый прогноз плавающего морского мусора. MIT-лицензия для кода, CC-BY-4.0 для уроков.</p>
          </div>
          <div>
            <div className="font-semibold text-zinc-700 dark:text-zinc-300 mb-2">Навигация</div>
            <ul className="space-y-1">
              <li><Link href="/map" className="hover:text-teal-700">Карта прогноза</Link></li>
              <li><Link href="/method" className="hover:text-teal-700">Метод (PINN)</Link></li>
              <li><Link href="/research" className="hover:text-teal-700">Наука</Link></li>
              <li><Link href="/ru/about" className="hover:text-teal-700">Об авторе</Link></li>
            </ul>
          </div>
          <div>
            <div className="font-semibold text-zinc-700 dark:text-zinc-300 mb-2">Контакты</div>
            <ul className="space-y-1">
              <li><a href={`mailto:${CONTACT_EMAIL}`} className="hover:text-teal-700">{CONTACT_EMAIL}</a></li>
              <li><a href={GITHUB} className="hover:text-teal-700">GitHub репозиторий</a></li>
              <li><Link href="/" className="hover:text-teal-700">English version</Link></li>
            </ul>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-zinc-200 dark:border-zinc-800 text-center">
          © 2026 TideGuard AI · MIT для кода · CC-BY-4.0 для контента
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
    <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="text-sm text-zinc-600 dark:text-zinc-400 mt-2 leading-relaxed">{body}</p>
    </div>
  );
}
