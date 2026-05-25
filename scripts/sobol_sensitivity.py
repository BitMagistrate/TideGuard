"""Sobol global sensitivity analysis of PINN forecasts.

Uses ``SALib`` to compute first-order (S1) and total (ST) Sobol indices
for three physical parameters that the PINN learns:

- ``alpha``: wind coupling (windage),
- ``K``: eddy diffusion,
- ``lam``: beaching rate.

We sample the parameter space with a Saltelli design, run the
forward model at each sample point, compute an aggregate output
(spatially-averaged concentration at t = horizon) and aggregate
sensitivities.

CLI::

    uv run python scripts/sobol_sensitivity.py \
        --checkpoint apps/ml/checkpoints/pinn_demo.pt \
        --out docs/sensitivity_sobol.json \
        --n 512

The default ``n=512`` produces 3584 model evaluations (Saltelli with
3 parameters), tractable on a CPU laptop in < 20 minutes for a small
PINN.

Outputs JSON with keys ``S1``, ``ST``, ``S2``, ``conf95`` per parameter
and a ``meta`` block.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ML_SRC = ROOT / "apps" / "ml" / "src"
sys.path.insert(0, str(ML_SRC))


def _forward(model, _x, grid_n: int = 32):
    import torch  # noqa: PLC0415

    xs = torch.linspace(0.0, 1.0, grid_n)
    ys = torch.linspace(0.0, 1.0, grid_n)
    gx, gy = torch.meshgrid(xs, ys, indexing="ij")
    t = torch.ones_like(gx) * 1.0  # horizon = 1.0 in normalised time
    return model(gx.flatten(), gy.flatten(), t.flatten()).reshape(grid_n, grid_n)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sobol sensitivity of PINN outputs.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--n", type=int, default=512, help="base sample size (Saltelli).")
    parser.add_argument("--horizon", type=float, default=1.0)
    parser.add_argument("--grid", type=int, default=32)
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "sensitivity_sobol.json")
    args = parser.parse_args(argv)

    try:
        from SALib.analyze.sobol import analyze as sobol_analyze  # type: ignore[import-not-found]
        from SALib.sample.sobol import sample as sobol_sample  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit("SALib not installed; `uv pip install SALib`") from exc
    try:
        import torch
    except ImportError as exc:
        raise SystemExit("torch not installed") from exc

    from tideguard_ml.pinn import PINN  # type: ignore[import-not-found]

    if not args.checkpoint.exists():
        raise SystemExit(f"--checkpoint not found: {args.checkpoint}")

    ckpt = torch.load(str(args.checkpoint), map_location="cpu", weights_only=True)
    state = ckpt["model_state_dict"]
    hidden = int(state["net.0.bias"].shape[0])
    in_dim = int(state["net.0.weight"].shape[1])
    num_freq = max(1, in_dim // 6)
    linear_idxs = sorted({int(k.split(".")[1]) for k in state if k.startswith("net.") and k.endswith(".weight")})
    depth = len(linear_idxs) - 1
    base_model = PINN(hidden=hidden, depth=depth, num_freq=num_freq)
    base_model.load_state_dict(state)
    base_model.eval()

    problem = {
        "num_vars": 3,
        "names": ["alpha", "K", "lam"],
        "bounds": [
            [1e-3, 5e-2],     # alpha — windage
            [1e-3, 1e-1],     # K — eddy diffusion
            [1e-4, 1e-2],     # lam — beaching rate
        ],
    }

    param_values = sobol_sample(problem, args.n, calc_second_order=True)
    y = []
    with torch.no_grad():
        for i, p in enumerate(param_values):
            alpha, K, lam = p
            base_model.log_alpha.data = torch.tensor(float(np.log(alpha)))  # type: ignore[name-defined]
            base_model.log_K.data = torch.tensor(float(np.log(K)))
            base_model.log_lam.data = torch.tensor(float(np.log(lam)))
            field = _forward(base_model, grid_n=args.grid)
            y.append(float(field.mean().item()))
            if i % 100 == 0:
                print(f"[sobol] {i}/{len(param_values)}", file=sys.stderr)

    y_arr = np.array(y, dtype=np.float64)  # type: ignore[name-defined]
    Si = sobol_analyze(problem, y_arr, calc_second_order=True, print_to_console=False)

    out = {
        "problem": problem,
        "S1": dict(zip(problem["names"], [float(v) for v in Si["S1"]], strict=False)),
        "ST": dict(zip(problem["names"], [float(v) for v in Si["ST"]], strict=False)),
        "S1_conf95": dict(zip(problem["names"], [float(v) for v in Si["S1_conf"]], strict=False)),
        "ST_conf95": dict(zip(problem["names"], [float(v) for v in Si["ST_conf"]], strict=False)),
        "S2": {
            "names": problem["names"],
            "matrix": [[float(v) for v in row] for row in Si["S2"]],
        },
        "meta": {
            "n_base_samples": args.n,
            "n_model_evals": len(param_values),
            "grid": args.grid,
            "horizon": args.horizon,
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(f"[sobol] wrote {args.out}")
    return 0


if __name__ == "__main__":
    import numpy as np  # noqa: F401 — used by inner scope

    raise SystemExit(main())
