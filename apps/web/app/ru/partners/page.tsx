import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Партнёры и сеть",
  description:
    "Экосистема TideGuard AI: поставщики данных, облачные спонсоры, школы, НКО и научные менторы. Каждый партнёр помечен честным статусом: активный / в обсуждении.",
  alternates: {
    canonical: "/ru/partners",
    languages: { "en-US": "/partners", "zh-TW": "/zh/partners" },
  },
};

const CONTACT_EMAIL = "scaleblinkk@vk.com";

type Partner = { name: string; status: "active" | "in-discussion"; blurb?: string };

type Category = { title: string; intro: string; items: Partner[] };

const CATEGORIES: Category[] = [
  {
    title: "Поставщики данных",
    intro:
      "Открытые научные источники, которые питают PINN. Все они используются прямо сейчас.",
    items: [
      { name: "Copernicus Marine Service (CMEMS)", status: "active", blurb: "Реанализ течений Чёрного моря" },
      { name: "ECMWF ERA5", status: "active", blurb: "Реанализ ветра на 10 м" },
      { name: "ESA Sentinel-2", status: "active", blurb: "Спутниковая детекция макропластика" },
      { name: "NEMO Black-Sea regional model (CMEMS)", status: "active", blurb: "Открытые региональные реанализы течений" },
      { name: "NOAA OISST", status: "active", blurb: "Температура поверхности моря" },
      { name: "Open-Meteo Marine API", status: "active", blurb: "Stokes drift (roadmap)" },
    ],
  },
  {
    title: "Облако и инфраструктурные спонсоры",
    intro:
      "Заявки на спонсорство поданы нескольким провайдерам. Каждый помечен реальным текущим статусом.",
    items: [
      { name: "Cloudflare (Project Galileo)", status: "in-discussion" },
      { name: "Vercel — OSS plan", status: "active", blurb: "Хостинг веба (free tier сейчас)" },
      { name: "Fly.io — Hobby plan", status: "active", blurb: "Хостинг API (free tier сейчас)" },
      { name: "Neon Postgres", status: "in-discussion" },
      { name: "GitHub Education", status: "in-discussion" },
      { name: "Sentry for OSS", status: "in-discussion" },
    ],
  },
  {
    title: "Академия и исследования",
    intro:
      "Исследователи, к которым мы обратились с шаблонными открытыми письмами поддержки. Никто ещё не подписал — основатель + AI-копилот, до-доходная фаза.",
    items: [
      { name: "Prof. Erik van Sebille (Utrecht)", status: "in-discussion", blurb: "Particle tracking и морской пластик" },
      { name: "Prof. Atsuhiko Isobe (Kyushu)", status: "in-discussion", blurb: "Количественная оценка плавающего мусора" },
      { name: "Российская академия наук — Институт океанологии", status: "in-discussion" },
      { name: "Университет «Сириус»", status: "in-discussion" },
    ],
  },
  {
    title: "Школы и НКО",
    intro:
      "Школы и НКО, с которыми мы обсуждаем пилотные уроки и уборки. Подписанных MoU ещё нет.",
    items: [
      { name: "Гимназия №13 «Академ», Красноярск", status: "active", blurb: "Школа основателя, пилот первого урока" },
      { name: "Гимназия города Анапа", status: "in-discussion" },
      { name: "«Чистые игры»", status: "in-discussion" },
      { name: "РГО — молодёжное отделение", status: "in-discussion" },
      { name: "Движение «ЭКА»", status: "in-discussion" },
    ],
  },
];

export default function RuPartnersPage() {
  return (
    <main className="min-h-screen">
      <section className="bg-gradient-to-br from-teal-700 to-ocean-600 text-white">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <p className="uppercase tracking-widest text-sand-100 text-xs mb-3">Партнёры</p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            С кем мы работаем. С кем хотим работать.
          </h1>
          <p className="text-lg text-sand-50 mt-6 max-w-3xl">
            <strong>Активных</strong> партнёров и партнёров{" "}
            <strong>в обсуждении</strong> мы отделяем явным значком — никаких
            раздутых стен логотипов. Хотите поддержать проект?{" "}
            <a href={`mailto:${CONTACT_EMAIL}`} className="underline">Напишите нам</a>.
          </p>
        </div>
      </section>

      {CATEGORIES.map((c) => (
        <section key={c.title} className="max-w-5xl mx-auto px-6 py-12">
          <h2 className="text-2xl font-bold">{c.title}</h2>
          <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">{c.intro}</p>
          <div className="grid md:grid-cols-2 gap-4 mt-6">
            {c.items.map((p) => (
              <div
                key={p.name}
                className="flex items-start justify-between gap-3 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-4"
              >
                <div>
                  <div className="font-semibold">{p.name}</div>
                  {p.blurb && <div className="text-sm text-zinc-500 mt-1">{p.blurb}</div>}
                </div>
                <StatusBadge status={p.status} />
              </div>
            ))}
          </div>
        </section>
      ))}

      <section className="bg-teal-700 text-white py-14">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold mb-3">Поддержите TideGuard.</h2>
          <p className="text-sand-100 mb-6">
            Все подписанные письма поддержки мы публикуем в{" "}
            <code>docs/letters_of_support/</code>. Шаблон письма на одну
            страницу есть в репозитории — форкайте.
          </p>
          <a
            href={`mailto:${CONTACT_EMAIL}?subject=Letter%20of%20Support%20%E2%80%94%20TideGuard%20AI`}
            className="inline-block px-5 py-3 bg-white text-teal-700 font-semibold rounded-lg"
          >
            Написать нам — {CONTACT_EMAIL}
          </a>
        </div>
      </section>
    </main>
  );
}

function StatusBadge({ status }: { status: "active" | "in-discussion" }) {
  if (status === "active") {
    return (
      <span className="shrink-0 inline-flex items-center rounded-full bg-teal-100 text-teal-700 text-xs px-2 py-0.5">
        Активный
      </span>
    );
  }
  return (
    <span className="shrink-0 inline-flex items-center rounded-full bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300 text-xs px-2 py-0.5">
      В обсуждении
    </span>
  );
}
