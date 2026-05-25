import Link from "next/link";

export const metadata = {
  title: "Как работает TideGuard — Physics-Informed Neural Network",
  description:
    "Нетехнический разбор PINN-модели TideGuard AI: физика, данные, базовые модели и неопределённость.",
  alternates: {
    canonical: "/ru/method",
    languages: { "en-US": "/method", "zh-TW": "/zh/method" },
  },
};

export default function RuMethodPage() {
  return (
    <main className="min-h-screen max-w-3xl mx-auto px-6 py-12 prose dark:prose-invert">
      <Link href="/ru" className="text-teal-700 text-sm no-underline">
        ← На главную
      </Link>
      <h1>Как работает TideGuard</h1>

      <div className="not-prose my-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-sand-50 dark:bg-zinc-900/60 text-left">
            <tr>
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
          </tbody>
        </table>
        <p className="text-xs text-zinc-500 px-4 py-3 border-t border-zinc-200 dark:border-zinc-800">
          Тест Диболда–Мариано против persistence: <code>p &lt; 3 × 10⁻¹¹²</code>.
          Синтетическая задача для Чёрного моря, ансамбль из 5 сидов, горизонт 14 дней.
          Препрегистрация на OSF. Полная таблица и bootstrap CI на{" "}
          <Link href="/ru/research#benchmark">/ru/research</Link>.
        </p>
      </div>

      <p>
        Прогноз TideGuard выдаёт <strong>Physics-Informed Neural Network (PINN)</strong>.
        Идея, предложенная{" "}
        <a
          href="https://www.sciencedirect.com/science/article/pii/S0021999118307125"
          target="_blank"
          rel="noopener"
        >
          Raissi, Perdikaris и Karniadakis (2019)
        </a>
        , объединяет гибкость нейронной сети и физические законы, которые мы уже
        знаем о системе. Сеть не просто учится по данным — она обязана
        удовлетворять уравнению в частных производных.
      </p>

      <h2>1. Физика</h2>
      <p>
        Плавающий мусор на поверхности океана переносится течениями, толкается
        ветром и медленно удаляется за счёт выноса на берег. Двумерное
        уравнение адвекции-диффузии, которое мы решаем:
      </p>
      <pre>
        ∂C/∂t + ∇·((u_ocean + α·u_wind) · C) − ∇·(K · ∇C) + λ · C = S(x, y, t)
      </pre>
      <ul>
        <li>
          <strong>C(x, y, t)</strong> — концентрация поверхностного мусора (нормирована в 0..1)
        </li>
        <li>
          <strong>u_ocean</strong> — поверхностное течение из{" "}
          <a href="https://marine.copernicus.eu/" target="_blank" rel="noopener">
            Copernicus Marine Service
          </a>
        </li>
        <li>
          <strong>u_wind</strong> — ветер на 10 м из{" "}
          <a
            href="https://cds.climate.copernicus.eu/"
            target="_blank"
            rel="noopener"
          >
            ECMWF ERA5
          </a>
        </li>
        <li>
          <strong>α, K, λ</strong> — коэффициенты windage, диффузии и выноса на берег.
          Они <em>обучаются из данных</em>, а не задаются заранее.
        </li>
        <li>
          <strong>S(x, y, t)</strong> — источники (например, реки); в синтетическом бенчмарке — ноль.
        </li>
      </ul>

      <h2>2. Модель</h2>
      <p>
        Шестислойный MLP по 128 скрытых юнитов на слой отображает (x, y, t) → C.
        Физические параметры живут как экспоненты трёх обучаемых скаляров
        (чтобы оставаться положительными). Код:{" "}
        <code>apps/ml/src/tideguard_ml/pinn.py</code>.
      </p>

      <h2>3. Функция потерь</h2>
      <p>
        Мы обучаем параллельно по четырём слагаемым: data term (соответствие
        наблюдениям), PDE residual (физика), initial-condition и
        boundary-condition. PyTorch вычисляет пространственные и временные
        производные через автоматическое дифференцирование.
      </p>

      <h2>4. Базовые модели</h2>
      <p>
        Каждой честной прогнозной статье нужны baseline-сравнения. Мы
        сравниваем PINN с:
      </p>
      <ul>
        <li>
          <strong>Persistence</strong>: завтра — как сегодня. Если мы не побеждаем эту модель,
          нас не нужно деплоить.
        </li>
        <li>
          <strong>Лагранжева трассировка частиц</strong>: та же физика, реализованная
          аналитически. Код:{" "}
          <code>apps/ml/src/tideguard_ml/baselines/lagrangian.py</code>.
        </li>
      </ul>
      <p>
        На синтетической тестовой задаче PINN выигрывает у persistence ≈ 28 %
        по RMSE и у лагранжевого baseline ≈ 12 % — см. полную таблицу в{" "}
        <code>docs/research_paper.md</code>.
      </p>

      <h2>5. Неопределённость и калибровка</h2>
      <p>
        Мы обучаем пять независимых сидов и сообщаем стандартное отклонение
        в каждом пикселе. Карта показывает и среднее ансамбля, и разброс — чтобы
        организаторы уборок видели, где модель уверена, а где гадает.
      </p>
      <p>
        Дополнительно мы считаем <strong>expected calibration error (ECE)</strong>
        {" "}на бинаризованной цели «top-10%» и при ECE &gt; 0.05 применяем
        post-hoc <strong>temperature scaling</strong> (Guo et al. 2017). Код:{" "}
        <code>apps/ml/src/tideguard_ml/eval/calibration.py</code>.
      </p>

      <h3>5.1 Вероятность превышения</h3>
      <p>
        Для планирования уборок практический вопрос — не «какова средняя
        концентрация?», а «какова вероятность, что данная клетка попадёт в
        верхние 10 % на следующей неделе?». Переключатель «P(exceed)» на{" "}
        <Link href="/map">/map</Link> показывает именно это, рассчитанное по
        пяти участникам ансамбля. Порог и квантиль настраиваются через API; см.{" "}
        <code>/forecast/exceedance</code> в OpenAPI-схеме.
      </p>

      <h2>6. Честные ограничения</h2>
      <ul>
        <li>Только глубинно-проинтегрированная модель — вертикальное оседание мы не моделируем.</li>
        <li>Источниковый член аппроксимирован; реки — главный TODO.</li>
        <li>Stokes drift от волн в roadmap (Open-Meteo Marine API уже подключён).</li>
        <li>
          Model card (<code>docs/model_card.md</code>) перечисляет известные
          смещения (географические, по охвату устройств, по самооценке тяжести).
        </li>
      </ul>

      <h2>7. Воспроизведение</h2>
      <pre>
        {`git clone https://github.com/BitMagistrate/TideGuard
cd TideGuard/apps/ml
uv venv && uv pip install -e ".[dev]"
uv run python -m tideguard_ml.train --synthetic --epochs 5000
uv run python -m tideguard_ml.baselines.benchmark --seeds 5`}
      </pre>

      <p className="text-sm text-zinc-500">
        Открыть код:{" "}
        <a href="https://github.com/BitMagistrate/TideGuard/tree/main/apps/ml">
          apps/ml на GitHub
        </a>
        .
      </p>
    </main>
  );
}
