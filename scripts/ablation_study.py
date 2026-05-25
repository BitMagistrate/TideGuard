"""Ablation study runner — turn off one PINN component at a time and
report the impact on RMSE / NSE.

Components ablated:
    A. data-loss-only (no PDE residual term)
    B. PDE-only (no data fit)
    C. no Fourier-feature embedding
    D. no boundary-condition term
    E. fixed parameters (no learnable α/K/λ)
    F. tiny network (hidden=32 instead of default 128)

Each variant runs at the same seed / epoch budget for a fair compare,
then a single JSON report is written.

CLI::

    uv run python scripts/ablation_study.py \
        --epochs 1000 --seeds 3 --out docs/ablation_latest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ML_SRC = ROOT / "apps" / "ml" / "src"
sys.path.insert(0, str(ML_SRC))


def _run_variant(name: str, *, epochs: int, seed: int, hidden: int, num_freq: int,
                 w_data: float, w_pde: float, w_ic: float, w_bc: float,
                 learnable_params: bool) -> dict:
    """Train one variant and return basic metrics on a synthetic eval grid."""
    import numpy as np
    import torch

    from tideguard_ml.pinn import PINN
    from tideguard_ml.train import TrainConfig, train

    torch.manual_seed(seed)
    np.random.seed(seed)

    cfg = TrainConfig(
        epochs=epochs,
        hidden=hidden,
        num_freq=num_freq,
        w_data=w_data,
        w_pde=w_pde,
        w_ic=w_ic,
        w_bc=w_bc,
        seed=seed,
        synthetic=True,
    )
    model = PINN(hidden=cfg.hidden, depth=6, num_freq=cfg.num_freq)
    if not learnable_params:
        # freeze the three log-parameters
        for p_name in ("log_alpha", "log_K", "log_lam"):
            param = getattr(model, p_name, None)
            if param is not None:
                param.requires_grad = False

    train(model, cfg)

    # eval on a coarse synthetic grid
    xs = torch.linspace(0.0, 1.0, 32)
    ys = torch.linspace(0.0, 1.0, 32)
    gx, gy = torch.meshgrid(xs, ys, indexing="ij")
    t = torch.ones_like(gx) * 1.0
    with torch.no_grad():
        pred = model(gx.flatten(), gy.flatten(), t.flatten()).reshape(32, 32).cpu().numpy()
    truth = np.exp(-((gx.numpy() - 0.5) ** 2 + (gy.numpy() - 0.5) ** 2) * 5.0)
    rmse = float(np.sqrt(((pred - truth) ** 2).mean()))
    nse = float(1 - ((pred - truth) ** 2).sum() / ((truth - truth.mean()) ** 2).sum())
    return {"variant": name, "seed": seed, "rmse": rmse, "nse": nse}


VARIANTS = [
    dict(name="A-data-only", w_data=1.0, w_pde=0.0, w_ic=1.0, w_bc=1.0,
         hidden=128, num_freq=8, learnable_params=True),
    dict(name="B-pde-only", w_data=0.0, w_pde=1.0, w_ic=1.0, w_bc=1.0,
         hidden=128, num_freq=8, learnable_params=True),
    dict(name="C-no-fourier", w_data=1.0, w_pde=0.1, w_ic=1.0, w_bc=1.0,
         hidden=128, num_freq=1, learnable_params=True),
    dict(name="D-no-bc", w_data=1.0, w_pde=0.1, w_ic=1.0, w_bc=0.0,
         hidden=128, num_freq=8, learnable_params=True),
    dict(name="E-fixed-params", w_data=1.0, w_pde=0.1, w_ic=1.0, w_bc=1.0,
         hidden=128, num_freq=8, learnable_params=False),
    dict(name="F-tiny", w_data=1.0, w_pde=0.1, w_ic=1.0, w_bc=1.0,
         hidden=32, num_freq=4, learnable_params=True),
    dict(name="full", w_data=1.0, w_pde=0.1, w_ic=1.0, w_bc=1.0,
         hidden=128, num_freq=8, learnable_params=True),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ablation study runner.")
    parser.add_argument("--epochs", type=int, default=1000)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "ablation_latest.json")
    args = parser.parse_args(argv)

    rows: list[dict] = []
    for variant in VARIANTS:
        for seed in range(args.seeds):
            row = _run_variant(epochs=args.epochs, seed=seed, **variant)
            rows.append(row)
            print(f"[ablation] {row}")

    # aggregate by variant
    summary: dict[str, dict] = {}
    for v in VARIANTS:
        sub = [r for r in rows if r["variant"] == v["name"]]
        if not sub:
            continue
        rmses = [r["rmse"] for r in sub]
        nses = [r["nse"] for r in sub]
        summary[v["name"]] = {
            "rmse_mean": sum(rmses) / len(rmses),
            "rmse_std": (sum((x - sum(rmses) / len(rmses)) ** 2 for x in rmses) / max(1, len(rmses) - 1)) ** 0.5,
            "nse_mean": sum(nses) / len(nses),
            "nse_std": (sum((x - sum(nses) / len(nses)) ** 2 for x in nses) / max(1, len(nses) - 1)) ** 0.5,
        }

    payload = {"runs": rows, "summary": summary, "epochs": args.epochs, "seeds": args.seeds}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2))
    print(f"[ablation] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
