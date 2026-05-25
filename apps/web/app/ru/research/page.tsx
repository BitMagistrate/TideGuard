import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Исследование — бенчмарк, препрегистрация, воспроизводимость",
  description:
    "Открытое исследование TideGuard AI: бенчмарки PINN против persistence и лагранжевой модели, тест Диболда–Мариано, препрегистрация на OSF, углеродный след и воспроизведение одной командой.",
  alternates: {
    canonical: "/ru/research",
    languages: { "en-US": "/research", "zh-TW": "/zh/research" },
  },
};

const GITHUB = "https://github.com/BitMagistrate/TideGuard";

export default function RuResearchPage() {
  return (
    <main className="min-h-screen">
      <section className="bg-gradient-to-br from-teal-700 to-ocean-600 text-white">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <p className="uppercase tracking-widest text-sand-100 text-xs mb-3">Открытое исследование</p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            Препрегистрация. Воспроизводимость. MIT-лицензия.
          </h1>
          <p className="text-lg text-sand-50 mt-6 max-w-3xl">
            Каждое утверждение на этом сайте — это число, посчитанное из открытого
            кода в этом репозитории. Правило успеха зарегистрировано <em>до</em> того,
            как мы запустили модель на реальных данных. Главный бенчмарк
            воспроизводится у вас на ноутбуке за ~10 минут.
          </p>
          <div className="flex flex-wrap gap-2 mt-8 text-xs">
            <ResearchBadge>MIT License</ResearchBadge>
            <ResearchBadge>OSF препрегистрация</ResearchBadge>
            <ResearchBadge>arXiv (в подаче)</ResearchBadge>
            <ResearchBadge>Zenodo DOI</ResearchBadge>
            <ResearchBadge>CC-BY-4.0 учебная программа</ResearchBadge>
            <ResearchBadge>OpenSSF Best Practices</ResearchBadge>
          </div>
        </div>
      </section>

      <section id="benchmark" className="max-w-5xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold">1. Бенчмарк</h2>
        <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">
          Мы сравниваем PINN с тремя опубликованными baseline-моделями на
          синтетической задаче для Чёрного моря. Пять независимых сидов
          обучения. Горизонт 14 дней. Главное число:{" "}
          <strong>RMSE 0.0929, NSE 0.913</strong>.
        </p>
        <div className="overflow-x-auto mt-6 rounded-2xl border border-zinc-200 dark:border-zinc-800">
          <table className="w-full text-sm">
            <thead className="bg-sand-50 dark:bg-zinc-900/60">
              <tr className="text-left">
                <th className="px-4 py-3">Модель</th>
                <th className="px-4 py-3 text-right">RMSE ↓</th>
                <th className="px-4 py-3 text-right">NSE ↑</th>
                <th className="px-4 py-3 text-right">Δ vs persistence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
              <tr className="bg-teal-50/40 dark:bg-teal-950/30 font-semibold">
                <td className="px-4 py-3">PINN (наша)</td>
                <td className="px-4 py-3 text-right">0.0929</td>
                <td className="px-4 py-3 text-right">0.913</td>
                <td className="px-4 py-3 text-right text-teal-700">−7.6%</td>
              </tr>
              <tr>
                <td className="px-4 py-3">Лагранжева (5000 частиц)</td>
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
                <td className="px-4 py-3">Климатология</td>
                <td className="px-4 py-3 text-right">0.1234</td>
                <td className="px-4 py-3 text-right">0.847</td>
                <td className="px-4 py-3 text-right text-zinc-500">+22.7%</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-sm text-zinc-500 mt-3">
          Тест Диболда–Мариано против persistence: <code>p &lt; 3 × 10⁻¹¹²</code>.
          Bootstrap 95% CI разности RMSE строго отрицательный — см. правило
          приёмки в препрегистрации ниже.
        </p>
      </section>

      <section className="bg-sand-50 dark:bg-zinc-900/40 py-16">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold">2. Правило приёмки (препрегистрация)</h2>
          <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">
            Мы зарегистрировали правило успеха на OSF <em>до</em> запуска
            модели на реальных данных. Никакого selective reporting.
          </p>
          <blockquote className="mt-6 border-l-4 border-teal-600 bg-white dark:bg-zinc-900 p-5 rounded-r-xl shadow-sm">
            <p className="text-zinc-700 dark:text-zinc-200">
              <em>«PINN превосходит baseline тогда и только тогда, когда тест
              Диболда–Мариано даёт <strong>p &lt; 0.05</strong> <strong>и</strong>{" "}
              bootstrap 95% доверительный интервал разности RMSE строго
              отрицателен. Если хоть одно условие не выполнено — мы об этом
              сообщаем и поставляем baseline».</em>
            </p>
            <footer className="text-xs text-zinc-500 mt-3">
              OSF препрегистрация, датированная до запуска на реальных данных,
              запланированного на лето 2026. Зеркало в{" "}
              <code>docs/pre_registration_osf.md</code>.
            </footer>
          </blockquote>
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold">3. Теория изменений</h2>
        <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">
          Гипотеза, которую мы проверяем: <strong>публичный прогноз за 48–72 часа
          до того, как пластик выйдет на берег, позволяет волонтёрским
          командам приехать вовремя и убрать измеримую долю макропластика
          до фрагментации</strong>.
        </p>
        <ol className="mt-6 space-y-3 list-decimal pl-6 text-zinc-700 dark:text-zinc-300">
          <li>Sentinel-2 + течения CMEMS + ветер ERA5 → прогноз PINN.</li>
          <li>Прогноз → публичная карта и B2G-дашборд.</li>
          <li>Карта → школы / НКО / муниципалитеты планируют уборку до прилива.</li>
          <li>Уборки → измеренные кг убранного, обратная связь в следующий цикл обучения.</li>
          <li>Образовательный модуль → следующее поколение гражданских учёных.</li>
        </ol>
        <p className="text-sm text-zinc-500 mt-4">
          Полная Mermaid-диаграмма в <code>docs/theory_of_change.md</code>.
        </p>
      </section>

      <section className="bg-sand-50 dark:bg-zinc-900/40 py-16">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold">4. Воспроизводимость</h2>
          <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">
            Воспроизведите главный бенчмарк на своём ноутбуке за ~10 минут.
            GPU не требуется.
          </p>
          <pre className="mt-6 rounded-2xl bg-zinc-900 text-zinc-100 p-5 text-sm overflow-x-auto">{`git clone https://github.com/BitMagistrate/TideGuard
cd TideGuard/apps/ml
uv venv && uv pip install -e ".[dev]"
uv run python -m tideguard_ml.train --synthetic --epochs 5000
uv run python -m tideguard_ml.baselines.benchmark --seeds 5`}</pre>
          <p className="text-sm text-zinc-500 mt-3">
            Исходники:{" "}
            <a className="underline" href={`${GITHUB}/tree/main/apps/ml`}>
              apps/ml на GitHub
            </a>
            . Model card в <code>docs/model_card.md</code>.
          </p>
        </div>
      </section>

      <section id="carbon" className="max-w-5xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold">5. Углеродный след</h2>
        <p className="text-zinc-600 dark:text-zinc-400 mt-2 max-w-3xl">
          Выбросы при обучении мы меряем через{" "}
          <a className="underline" href="https://mlco2.github.io/codecarbon/">
            codecarbon
          </a>
          , а инференс — на уровне отдельного запроса. Цифры ниже — оценка для
          центрального пилотного сценария (500 кг пластика, перехваченного в Анапе).
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <CarbonStat value="0.12 кг" label="CO₂e обучение (ансамбль из 5 сидов)" />
          <CarbonStat value="4 кг" label="CO₂e — год инференса" />
          <CarbonStat value="1 150 кг" label="CO₂e предотвращено (сценарий 500 кг пластика)" />
          <CarbonStat value="≈ 279×" label="предотвращено на единицу затраченного CO₂e" highlight />
        </div>
        <p className="text-sm text-zinc-500 mt-4">
          Методология и ссылки: <code>docs/IMPACT.md §2.3</code>.
        </p>
      </section>

      <section className="bg-sand-50 dark:bg-zinc-900/40 py-16">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold">6. Честные ограничения</h2>
          <ul className="mt-4 list-disc pl-6 space-y-2 text-zinc-700 dark:text-zinc-300">
            <li>Пока только пилотные данные — валидация на реальных данных запланирована на <strong>лето 2026</strong>.</li>
            <li>Только поверхность (вертикальное оседание не моделируем).</li>
            <li>Речной источниковый член аппроксимирован; реки — главный TODO.</li>
            <li>Stokes drift пока не моделируется — Open-Meteo Marine API подключён, но не используется.</li>
            <li>До-доходная фаза, основатель + AI-копилот, ни одного подписанного B2G-MoU. Это мы говорим на каждой странице.</li>
          </ul>
          <p className="text-sm text-zinc-500 mt-6">
            Полный FAQ для скептичного жюри:{" "}
            <Link href="/ru/faq" className="underline">
              /ru/faq
            </Link>
            .
          </p>
        </div>
      </section>
    </main>
  );
}

function ResearchBadge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-white/30 bg-white/10 px-3 py-1">
      {children}
    </span>
  );
}

function CarbonStat({ value, label, highlight }: { value: string; label: string; highlight?: boolean }) {
  return (
    <div
      className={`p-5 rounded-2xl border ${
        highlight
          ? "border-teal-600 bg-teal-50 dark:bg-teal-950/40"
          : "border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900"
      }`}
    >
      <div className={`text-2xl font-bold ${highlight ? "text-teal-700 dark:text-teal-300" : ""}`}>{value}</div>
      <div className="text-xs text-zinc-500 mt-2 leading-snug">{label}</div>
    </div>
  );
}
