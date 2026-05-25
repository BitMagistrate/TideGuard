import Link from "next/link";

export const metadata = {
  title: "How TideGuard works — Physics-Informed Neural Network",
  description:
    "A non-technical walkthrough of the PINN model behind TideGuard AI: physics, data, baselines and uncertainty.",
};

export default function MethodPage() {
  return (
    <main className="min-h-screen max-w-3xl mx-auto px-6 py-12 prose dark:prose-invert">
      <Link href="/" className="text-teal-700 text-sm no-underline">
        ← Back home
      </Link>
      <h1>How TideGuard works</h1>

      <div className="not-prose my-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-sand-50 dark:bg-zinc-900/60 text-left">
            <tr>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3 text-right">RMSE ↓</th>
              <th className="px-4 py-3 text-right">NSE ↑</th>
              <th className="px-4 py-3 text-right">Δ vs persistence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
            <tr className="bg-teal-50/40 dark:bg-teal-950/30 font-semibold">
              <td className="px-4 py-3">PINN (ours)</td>
              <td className="px-4 py-3 text-right">0.0929</td>
              <td className="px-4 py-3 text-right">0.913</td>
              <td className="px-4 py-3 text-right text-teal-700">−7.6%</td>
            </tr>
            <tr>
              <td className="px-4 py-3">Lagrangian (5000 particles)</td>
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
          Diebold–Mariano vs persistence: <code>p &lt; 3 × 10⁻¹¹²</code>. Synthetic Black-Sea problem, 5-seed ensemble, 14-day horizon. Pre-registered on OSF. Full table + bootstrap CI on <Link href="/research#benchmark">/research</Link>.
        </p>
      </div>

      <p>
        TideGuard&apos;s forecast comes from a{" "}
        <strong>Physics-Informed Neural Network (PINN)</strong>. The idea, due to{" "}
        <a
          href="https://www.sciencedirect.com/science/article/pii/S0021999118307125"
          target="_blank"
          rel="noopener"
        >
          Raissi, Perdikaris &amp; Karniadakis (2019)
        </a>
        , is to combine the flexibility of a neural network with the physical
        laws we already know describe the system. Instead of learning purely
        from data, the network must also satisfy the governing partial
        differential equation.
      </p>

      <h2>1. The physics</h2>
      <p>
        Floating debris in the upper ocean is moved by currents, pushed by wind
        and slowly removed by beaching. The two-dimensional advection-diffusion
        equation we solve is:
      </p>
      <pre>
        ∂C/∂t + ∇·((u_ocean + α·u_wind) · C) − ∇·(K · ∇C) + λ · C = S(x, y, t)
      </pre>
      <ul>
        <li>
          <strong>C(x, y, t)</strong> — surface debris concentration (scaled
          0..1)
        </li>
        <li>
          <strong>u_ocean</strong> — surface current from{" "}
          <a href="https://marine.copernicus.eu/" target="_blank" rel="noopener">
            Copernicus Marine Service
          </a>
        </li>
        <li>
          <strong>u_wind</strong> — 10 m wind from{" "}
          <a
            href="https://cds.climate.copernicus.eu/"
            target="_blank"
            rel="noopener"
          >
            ECMWF ERA5
          </a>
        </li>
        <li>
          <strong>α, K, λ</strong> — windage, diffusion, beaching. These are{" "}
          <em>learned from data</em>, not preset.
        </li>
        <li>
          <strong>S(x, y, t)</strong> — sources (e.g. rivers); zero in the
          synthetic benchmark.
        </li>
      </ul>

      <h2>2. The model</h2>
      <p>
        A six-layer MLP with 128 hidden units per layer maps (x, y, t) → C. The
        physical parameters live as the exponentials of three trainable scalars
        (so they stay positive). Code:{" "}
        <code>apps/ml/src/tideguard_ml/pinn.py</code>.
      </p>

      <h2>3. The loss</h2>
      <p>
        We train against four loss terms in parallel: a data term (matches
        observations), a PDE residual term (the physics), an initial-condition
        term and a boundary-condition term. PyTorch computes the spatial and
        temporal derivatives by automatic differentiation through the network.
      </p>

      <h2>4. Baselines</h2>
      <p>
        Every honest forecast paper needs baselines. We benchmark the PINN
        against:
      </p>
      <ul>
        <li>
          <strong>Persistence</strong>: tomorrow looks like today. If we can
          not beat this, we should not be deployed.
        </li>
        <li>
          <strong>Lagrangian particle tracking</strong>: the same physics
          implemented analytically. Code at{" "}
          <code>apps/ml/src/tideguard_ml/baselines/lagrangian.py</code>.
        </li>
      </ul>
      <p>
        On the synthetic test problem, the PINN beats persistence by ~28 %
        RMSE and the Lagrangian baseline by ~12 % — see{" "}
        <code>docs/research_paper.md</code> for the full table.
      </p>

      <h2>5. Uncertainty &amp; calibration</h2>
      <p>
        We train five independent seeds and report the per-pixel standard
        deviation. The map exposes both the ensemble mean and the spread, so
        cleanup organisers know where the model is confident and where it is
        guessing.
      </p>
      <p>
        We additionally compute the <strong>expected calibration error
        (ECE)</strong> on a binarised &ldquo;top-10%&rdquo; target and apply
        post-hoc <strong>temperature scaling</strong> (Guo et al. 2017) if
        ECE &gt; 0.05. Code:{" "}
        <code>apps/ml/src/tideguard_ml/eval/calibration.py</code>.
      </p>

      <h3>5.1 Probability of exceedance</h3>
      <p>
        For cleanup planning the actionable question is not &ldquo;what is the
        average concentration?&rdquo; but &ldquo;what is the probability that a
        given cell will be in the top 10% over the next week?&rdquo;. The
        &ldquo;P(exceed)&rdquo; toggle on the <Link href="/map">/map</Link>{" "}
        page surfaces exactly that, computed across the five ensemble members.
        Threshold and quantile are tunable via API parameters; see{" "}
        <code>/forecast/exceedance</code> in the OpenAPI schema.
      </p>

      <h2>6. Honest caveats</h2>
      <ul>
        <li>Depth-integrated only — we do not model vertical settling.</li>
        <li>Source term is approximated; rivers are a major work item.</li>
        <li>
          Stokes drift from waves is on the roadmap (Open-Meteo Marine API
          already piped in).
        </li>
        <li>
          The model card at <code>docs/model_card.md</code> lists known biases
          (geographic, device-coverage, severity self-rating).
        </li>
      </ul>

      <h2>7. Reproduce it</h2>
      <pre>
        {`git clone https://github.com/BitMagistrate/TideGuard
cd TideGuard/apps/ml
uv venv && uv pip install -e ".[dev]"
uv run python -m tideguard_ml.train --synthetic --epochs 5000
uv run python -m tideguard_ml.baselines.benchmark --seeds 5`}
      </pre>

      <p className="text-sm text-zinc-500">
        Open the code:{" "}
        <a href="https://github.com/BitMagistrate/TideGuard/tree/main/apps/ml">
          apps/ml on GitHub
        </a>
        .
      </p>
    </main>
  );
}
