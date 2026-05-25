import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Lesson = { id: string; slug: string; title: string; xp_reward: number; order: number };

type Lang = "en" | "ru" | "zh-TW";

const FALLBACK_LESSONS_EN: Lesson[] = [
  { id: "1", slug: "marine-plastic", title: "What is marine plastic and why it matters", xp_reward: 50, order: 1 },
  { id: "2", slug: "lifecycle", title: "The lifecycle of plastic in the ocean", xp_reward: 50, order: 2 },
  { id: "3", slug: "microplastic-food", title: "Microplastic and the food chain", xp_reward: 50, order: 3 },
  { id: "4", slug: "read-the-map", title: "How to read the TideGuard map", xp_reward: 50, order: 4 },
  { id: "5", slug: "good-report", title: "How to make a quality citizen report", xp_reward: 50, order: 5 },
  { id: "6", slug: "safety", title: "Safety during a cleanup", xp_reward: 50, order: 6 },
  { id: "7", slug: "organize-cleanup", title: "Organizing a local cleanup event", xp_reward: 50, order: 7 },
  { id: "8", slug: "sort-waste", title: "Sorting collected waste", xp_reward: 50, order: 8 },
  { id: "9", slug: "reduce-reuse", title: "Reduce / Reuse / Recycle for teens", xp_reward: 50, order: 9 },
  { id: "10", slug: "lead-school", title: "Becoming a leader in your school", xp_reward: 50, order: 10 },
];

const FALLBACK_LESSONS_RU: Lesson[] = [
  { id: "1", slug: "marine-plastic", title: "Морской пластик: что это и почему важно", xp_reward: 50, order: 1 },
  { id: "2", slug: "lifecycle", title: "Жизненный цикл пластика в океане", xp_reward: 50, order: 2 },
  { id: "3", slug: "microplastic-food", title: "Микропластик и пищевая цепочка", xp_reward: 50, order: 3 },
  { id: "4", slug: "read-the-map", title: "Как читать карту TideGuard", xp_reward: 50, order: 4 },
  { id: "5", slug: "good-report", title: "Как сделать качественный гражданский репорт", xp_reward: 50, order: 5 },
  { id: "6", slug: "safety", title: "Безопасность во время уборки", xp_reward: 50, order: 6 },
  { id: "7", slug: "organize-cleanup", title: "Как организовать уборку в своём районе", xp_reward: 50, order: 7 },
  { id: "8", slug: "sort-waste", title: "Сортировка собранного мусора", xp_reward: 50, order: 8 },
  { id: "9", slug: "reduce-reuse", title: "Reduce / Reuse / Recycle для подростков", xp_reward: 50, order: 9 },
  { id: "10", slug: "lead-school", title: "Стать лидером изменений в своей школе", xp_reward: 50, order: 10 },
];

const FALLBACK_LESSONS_ZH: Lesson[] = [
  { id: "1", slug: "marine-plastic", title: "海洋塑膠：什麼是海洋塑膠，為何重要", xp_reward: 50, order: 1 },
  { id: "2", slug: "lifecycle", title: "塑膠在海洋中的生命週期", xp_reward: 50, order: 2 },
  { id: "3", slug: "microplastic-food", title: "微塑膠與食物鏈", xp_reward: 50, order: 3 },
  { id: "4", slug: "read-the-map", title: "如何閱讀 TideGuard 地圖", xp_reward: 50, order: 4 },
  { id: "5", slug: "good-report", title: "如何提交高品質的公民通報", xp_reward: 50, order: 5 },
  { id: "6", slug: "safety", title: "淨灘期間的安全", xp_reward: 50, order: 6 },
  { id: "7", slug: "organize-cleanup", title: "組織在地淨灘活動", xp_reward: 50, order: 7 },
  { id: "8", slug: "sort-waste", title: "分類收集的垃圾", xp_reward: 50, order: 8 },
  { id: "9", slug: "reduce-reuse", title: "青少年的 Reduce / Reuse / Recycle", xp_reward: 50, order: 9 },
  { id: "10", slug: "lead-school", title: "在學校中成為領導者", xp_reward: 50, order: 10 },
];

async function fetchLessons(lang: Lang): Promise<Lesson[]> {
  try {
    const res = await fetch(`${API}/education/lessons?lang=${lang}`, { next: { revalidate: 60 } });
    if (!res.ok) throw new Error("not ok");
    const list = (await res.json()) as Lesson[];
    if (!list?.length) throw new Error("empty");
    return list;
  } catch {
    if (lang === "ru") return FALLBACK_LESSONS_RU;
    if (lang === "zh-TW") return FALLBACK_LESSONS_ZH;
    return FALLBACK_LESSONS_EN;
  }
}

type SearchParams = { lang?: string };

function detectLang(raw?: string): Lang {
  if (raw === "ru") return "ru";
  if (raw === "zh" || raw === "zh-TW" || raw === "zh-Hant") return "zh-TW";
  return "en";
}

export default async function LearnPage({ searchParams }: { searchParams?: SearchParams }) {
  const lang: Lang = detectLang(searchParams?.lang);
  const lessons = await fetchLessons(lang);
  const t =
    lang === "ru"
      ? {
          back: "← На главную",
          backHref: "/ru",
          title: "Экологическое образование",
          sub: "10 уроков (~5 минут каждый). В конце каждого — 5-вопросный квиз и практическое задание. Пройди 5 уроков — получи сертификат TideGuard.",
          lessonWord: "Урок",
        }
      : lang === "zh-TW"
      ? {
          back: "← 返回首頁",
          backHref: "/zh",
          title: "環境教育",
          sub: "10 堂課程 (每堂約 5 分鐘)。每堂結束有 5 題測驗與一項實作任務。完成 5 堂課可解鎖 TideGuard 證書。",
          lessonWord: "課程",
        }
      : {
          back: "← Back home",
          backHref: "/",
          title: "Environmental Education",
          sub: "10 lessons (~5 minutes each). Each ends with a 5-question quiz and a practical task. Complete 5 lessons to unlock your TideGuard certificate.",
          lessonWord: "Lesson",
        };

  const langSuffix =
    lang === "ru" ? "?lang=ru" : lang === "zh-TW" ? "?lang=zh-TW" : "";

  return (
    <main className="min-h-screen max-w-4xl mx-auto px-6 py-12">
      <div className="flex items-center justify-between mb-2">
        <Link href={t.backHref} className="text-teal-700 text-sm">
          {t.back}
        </Link>
        <div className="flex gap-1 text-xs">
          <Link
            href="/learn?lang=en"
            className={`px-2 py-1 rounded ${
              lang === "en"
                ? "bg-teal-700 text-white"
                : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300"
            }`}
          >
            EN
          </Link>
          <Link
            href="/learn?lang=ru"
            className={`px-2 py-1 rounded ${
              lang === "ru"
                ? "bg-teal-700 text-white"
                : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300"
            }`}
          >
            RU
          </Link>
          <Link
            href="/learn?lang=zh-TW"
            className={`px-2 py-1 rounded ${
              lang === "zh-TW"
                ? "bg-teal-700 text-white"
                : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300"
            }`}
          >
            ZH
          </Link>
        </div>
      </div>
      <h1 className="text-4xl font-bold mt-2 mb-3">{t.title}</h1>
      <p className="text-zinc-600 dark:text-zinc-400 mb-8 max-w-2xl">{t.sub}</p>

      <ol className="space-y-3">
        {lessons.map((l) => (
          <li
            key={l.slug}
            className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 flex justify-between items-center bg-white dark:bg-zinc-900"
          >
            <div>
              <div className="text-xs uppercase tracking-wider text-zinc-500">
                {t.lessonWord} {l.order}
              </div>
              <Link
                href={`/learn/${l.slug}${langSuffix}`}
                className="text-lg font-semibold hover:text-teal-700"
              >
                {l.title}
              </Link>
            </div>
            <div className="text-sm text-teal-700 font-medium">+{l.xp_reward} XP</div>
          </li>
        ))}
      </ol>
    </main>
  );
}
