import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Пресс-кит",
  description:
    "Boilerplate, готовые к цитированию аннотации, ключевые цифры и брендовые ассеты для журналистов, освещающих TideGuard AI.",
  alternates: {
    canonical: "/ru/press",
    languages: { "en-US": "/press", "zh-TW": "/zh/press" },
  },
};

const CONTACT_EMAIL = "scaleblinkk@vk.com";
const GITHUB = "https://github.com/BitMagistrate/TideGuard";

export default function RuPressPage() {
  return (
    <main className="min-h-screen">
      <section className="bg-gradient-to-br from-teal-700 to-ocean-600 text-white">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <p className="uppercase tracking-widest text-sand-100 text-xs mb-3">Пресс-кит</p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            Цитируйте корректно. Цитируйте свободно.
          </h1>
          <p className="text-lg text-sand-50 mt-6 max-w-3xl">
            Весь контент на этой странице — под CC-BY-4.0. Можно использовать
            в статьях, рассылках, школьных газетах. Контакт для прессы:{" "}
            <a href={`mailto:${CONTACT_EMAIL}`} className="underline">{CONTACT_EMAIL}</a>.
          </p>
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-6 py-16 space-y-12">
        <Block title="Лифтовый питч на 60 слов">
          <p>
            TideGuard AI — это open-source прогноз плавающего пластика на побережье
            Чёрного моря. Physics-Informed нейросеть объединяет спутниковые снимки,
            океанические течения и гражданские репорты, чтобы предсказывать «горячие
            точки» мусора за 48–72 часа до прилива. Платформа бесплатна, MIT-лицензия,
            создана 17-летним школьником из Красноярска с AI-копилотом.
          </p>
        </Block>

        <Block title="Аннотация на 120 слов">
          <p>
            TideGuard AI — первый региональный open-science прогноз плавающего
            морского мусора на Чёрном море. Модель решает 2D уравнение
            адвекции-диффузии для концентрации поверхностного пластика
            физико-информированной нейросетью: коэффициенты windage, eddy diffusion
            и скорости выноса на берег обучаются непосредственно из данных. На
            ансамбле из пяти сидов синтетического бенчмарка PINN бьёт persistence с{" "}
            <code>p &lt; 3×10⁻¹¹²</code> (Диболд–Мариано) на горизонте 14 дней.
            Платформа объединяет прогноз с бесплатным курсом из 10 уроков на
            английском, русском и китайском и B2G-дашбордом для муниципалитетов.
            Собран Владимиром Ермоленко (17, Красноярск), MIT-лицензия, OSF
            препрегистрация, без патентов.
          </p>
        </Block>

        <Block title="Ключевые цифры (свободно для цитирования)">
          <ul className="list-disc pl-6 space-y-1">
            <li>PINN: RMSE 0.0929, NSE 0.913 на синтетической задаче для Чёрного моря.</li>
            <li>На 7.6% по RMSE превосходит persistence, на 4.4% — лагранжев baseline.</li>
            <li>Статистическая значимость: <code>p &lt; 3 × 10⁻¹¹²</code> (Диболд–Мариано).</li>
            <li>540+ одно-километровых сегментов берега в 22 городах.</li>
            <li>10 уроков × 3 языка = 30 модулей.</li>
            <li>Углеродный след обучения: 0.12 кг CO₂e; коэффициент предотвращения ≈ 279×.</li>
            <li>Прогноз ROI пилота в Анапе: 304% за 2.97 месяца.</li>
            <li>Основатель + AI, MIT-код, CC-BY-4.0 уроки.</li>
          </ul>
        </Block>

        <Block title="Основатель">
          <p>
            <strong>Владимир Ермоленко</strong> (Ермоленко Владимир Александрович),
            17 лет, 10 класс, Гимназия №13 «Академ», Красноярск. Собрал TideGuard
            за 3 месяца с AI-копилотом. Доступен для интервью на русском или английском.
          </p>
          <p className="mt-2">
            Полная история основателя:{" "}
            <Link href="/ru/about" className="underline">/ru/about</Link> (RU) ·{" "}
            <Link href="/about" className="underline">/about</Link> (EN).
          </p>
        </Block>

        <Block title="Брендовые ассеты">
          <ul className="list-disc pl-6 space-y-1">
            <li>Open-graph карточка: <code>/og-image.png</code> (1200×630)</li>
            <li>Favicon: <code>/favicon.ico</code></li>
            <li>Primary teal: <code>#0b5550</code> · Ocean blue: <code>#025980</code> · Sand: <code>#FEF8E7</code></li>
            <li>Репозиторий: <a href={GITHUB} className="underline">{GITHUB}</a></li>
          </ul>
        </Block>

        <Block title="Boilerplate (1 абзац, для секции «О проекте» в статье)">
          <p>
            TideGuard AI — это open-source платформа, которая прогнозирует
            плавающий морской пластик на побережье Чёрного моря за 48–72 часа до
            выхода на берег, используя физико-информированную нейросеть поверх
            бесплатных спутниковых и океанографических данных. Платформа
            объединяет публичную карту, курс из 10 уроков на трёх языках и
            муниципальный дашборд. Код — под MIT, контент — под CC-BY-4.0; все
            бенчмарки воспроизводятся одной командой. TideGuard был собран
            17-летним Владимиром Ермоленко (Красноярск, Россия) с AI-копилотом и
            заранее зарегистрирован на Open Science Framework.
          </p>
        </Block>
      </section>

      <section className="bg-teal-700 text-white py-14">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold mb-3">Нужна цитата, интервью или сырые данные?</h2>
          <p className="text-sand-100 mb-6">
            Отвечаем за 48 часов на русском или английском. В теме письма
            укажите издание и дедлайн.
          </p>
          <a
            href={`mailto:${CONTACT_EMAIL}?subject=Press%20enquiry%20%E2%80%94%20TideGuard%20AI`}
            className="inline-block px-5 py-3 bg-white text-teal-700 font-semibold rounded-lg"
          >
            {CONTACT_EMAIL}
          </a>
        </div>
      </section>
    </main>
  );
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
      <h2 className="text-xl font-semibold">{title}</h2>
      <div className="mt-3 text-zinc-700 dark:text-zinc-300 leading-relaxed">{children}</div>
    </div>
  );
}
