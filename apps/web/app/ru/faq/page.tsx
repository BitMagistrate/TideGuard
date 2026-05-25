"use client";

import { useState } from "react";
import Link from "next/link";

type QA = { q: string; a: React.ReactNode };

const FAQS: QA[] = [
  {
    q: "А если PINN на реальных данных всё-таки не побьёт persistence?",
    a: (
      <>
        <p>
          Ровно для этого и нужно правило приёмки, заранее зарегистрированное на OSF.
          Правило: PINN превосходит baseline тогда и только тогда, когда тест
          Диболда–Мариано даёт <code>p &lt; 0.05</code> <em>и</em> bootstrap 95% CI
          разности RMSE строго отрицателен. Если на запуске по реальным
          данным (лето 2026) это не выполнится — публикуем негативный
          результат и поставляем baseline.
        </p>
        <p className="mt-2">
          Негативный результат <em>не</em> убивает проект. Платформа — карта,
          уроки, гражданские репорты, B2G-дашборд — работает поверх любой
          прогнозной модели, включая аналитический лагранжев baseline.
        </p>
      </>
    ),
  },
  {
    q: "А как мы поймём, что вы не подкрутили модель под красивые цифры?",
    a: (
      <p>
        Потому что правило приёмки зарегистрировано на OSF <em>до</em> запуска
        на реальных данных, а бенчмарк воспроизводится у любого за ~10 минут
        одной командой — см.{" "}
        <Link href="/ru/research#benchmark" className="underline">/ru/research</Link>.
        Весь код обучения и оценки — под MIT-лицензией в репозитории.
      </p>
    ),
  },
  {
    q: "Почему именно PINN, а не обычная DL-модель?",
    a: (
      <p>
        У чисто data-driven сети не на что опереться вне обучающего
        распределения. PDE-residual в loss заставляет сеть уважать закон
        сохранения массы и физику переноса — именно это даёт экстраполяцию
        на свежие штормы и новые участки берега. Чистые ML-модели,
        которые мы пробовали, переобучались на синтетический шум; PINN — нет.
      </p>
    ),
  },
  {
    q: "Что будет, когда основатель уйдёт в университет?",
    a: (
      <p>
        Всё открыто, под MIT, с публичным roadmap и CI на каждый коммит.
        Проект спроектирован под преемственность: гайд по контрибуции в{" "}
        <code>CONTRIBUTING.md</code>, governance в{" "}
        <code>docs/scaling_plan_2026_2029.md</code>. Я активно ищу двух
        со-лидов своего возраста именно для того, чтобы проект не зависел
        от меня. Платформа портируется на нового мейнтейнера за выходные.
      </p>
    ),
  },
  {
    q: "Кто вы такие, чтобы соревноваться с The Ocean Cleanup и Plastic Drift?",
    a: (
      <p>
        Мы не соревнуемся — эти проекты делают другие вещи. The Ocean Cleanup
        убирает пластик в открытом океане, Plastic Drift строит глобальные
        траектории, Global Plastic Watch со спутника находит наземные свалки.
        Ни один из них не выпускает публичный региональный прогноз для
        Чёрного моря с учётом неопределённости, паре с бесплатной K-12
        учебной программой и B2G-дашбордом. Этот пробел и закрывает TideGuard.
      </p>
    ),
  },
  {
    q: "Как соблюдается 152-ФЗ (РФ) и GDPR?",
    a: (
      <p>
        Гражданские репорты псевдонимны по конструкции. Мы храним только то,
        что нужно для прогноза: грубые координаты, hash фото и общий fingerprint
        устройства. Политика по этике данных:{" "}
        <code>docs/DATA_ETHICS.md</code>; конспект по GDPR:{" "}
        <code>docs/GDPR_COMPLIANCE.md</code>. Персональные данные пользователей
        ЕС обрабатываются на инфраструктуре в ЕС, с удалением в один клик.
      </p>
    ),
  },
  {
    q: "А если из-за санкций пропадёт доступ к Sentinel или CMEMS?",
    a: (
      <p>
        У нас есть документированный contingency: degraded-режим, в котором
        работает только ERA5 + открытые AIS / наблюдения с попутных судов до
        возвращения официальных фидов. Risk register в{" "}
        <code>docs/risk_register.md</code> описывает три независимых пути
        отказа и соответствующие fallback-модели.
      </p>
    ),
  },
  {
    q: "Вы реально один основатель + AI-копилот?",
    a: (
      <p>
        Да. Никакой ghost-команды, никакого агентства, никакой материнской
        организации. Мне 17 лет, я собрал кодовую базу один за 3 месяца на
        одном ноутбуке. Никому ничего не платил и от никого не получал
        вознаграждения за эту работу. Ищу 1–2 со-лидов своего возраста и
        академического ментора — см. <Link href="/ru/about" className="underline">/ru/about</Link>.
      </p>
    ),
  },
  {
    q: "Это прибыльно?",
    a: (
      <p>
        Нет, и мы никогда не заявляли обратного. TideGuard — до-доходный.
        На странице цен показаны прогнозные юнит-экономики: blended-выручка
        Year-1 <em>прогнозируется</em> на уровне €270k от B2G-подписок и
        грантов. Публичный прогноз и образовательный модуль останутся
        бесплатными по лицензии, независимо от платных тарифов.
      </p>
    ),
  },
];

export default function RuFAQPage() {
  return (
    <main className="min-h-screen">
      <section className="bg-gradient-to-br from-teal-700 to-ocean-600 text-white">
        <div className="max-w-5xl mx-auto px-6 py-20">
          <p className="uppercase tracking-widest text-sand-100 text-xs mb-3">
            Сложные вопросы
          </p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            Ответы на те вопросы, которые жюри действительно задаст.
          </h1>
          <p className="text-lg text-sand-50 mt-6 max-w-3xl">
            Мы заранее отвечаем на самые неудобные вопросы — про
            препрегистрацию, fallback-модели, преемственность, governance и
            почему мы не подобрали бенчмарк сами для себя.
          </p>
        </div>
      </section>

      <section className="max-w-3xl mx-auto px-6 py-16 space-y-3">
        {FAQS.map((qa, i) => (
          <FAQItem key={i} qa={qa} />
        ))}
      </section>

      <section className="bg-sand-50 dark:bg-zinc-900/40 py-14">
        <div className="max-w-3xl mx-auto px-6 text-center text-sm text-zinc-600 dark:text-zinc-400">
          Есть вопрос ещё жёстче? Пишите на{" "}
          <a href="mailto:scaleblinkk@vk.com" className="underline">scaleblinkk@vk.com</a> —
          отвечаем за 48 часов.
        </div>
      </section>
    </main>
  );
}

function FAQItem({ qa }: { qa: QA }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-3 px-5 py-4 text-left"
        aria-expanded={open}
      >
        <span className="font-semibold">{qa.q}</span>
        <span className="text-teal-700 text-xl shrink-0">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <div className="px-5 pb-5 text-zinc-700 dark:text-zinc-300 leading-relaxed text-[15px]">
          {qa.a}
        </div>
      )}
    </div>
  );
}
