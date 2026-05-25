"""Benchmark harness — compare PINN vs persistence vs Lagrangian baselines.

Usage::

    python -m tideguard_ml.baselines.benchmark --seeds 5 --horizon 7

Prints an RMSE / NSE table to stdout and writes a JSON summary to
``apps/ml/benchmarks/latest.json``. The synthetic dataset gives us a known
ground truth; numbers reported in ``docs/research_paper.md`` come from this
script.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import torch

from tideguard_ml.baselines.climatology import ClimatologyBaseline
from tideguard_ml.baselines.lagrangian import LagrangianBaseline
from tideguard_ml.baselines.persistence import PersistenceBaseline
from tideguard_ml.data import SyntheticDataset
from tideguard_ml.pinn import PINN
from tideguard_ml.train import TrainConfig, train


@dataclass
class BenchmarkResult:
    model: str
    horizon: int
    rmse: float
    nse: float  # Nash-Sutcliffe efficiency, higher is better
    seeds: int


def _ground_truth_grid(ds: SyntheticDataset, horizon: int, n: int = 32) -> np.ndarray:
    """Replicate the synthetic dataset's analytic Gaussian on a regular grid."""
    grid = np.linspace(0, 1, n)
    xx, yy = np.meshgrid(grid, grid)
    out = np.zeros((horizon, n, n), dtype=np.float32)
    u_eff = ds.u_ocean + ds.alpha_true * ds.u_wind
    v_eff = ds.v_ocean + ds.alpha_true * ds.v_wind
    for d in range(horizon):
        t = d / 14.0
        cx = 0.3 + u_eff * t
        cy = 0.5 + v_eff * t
        sigma = 0.05 + 2 * ds.K_true * t
        out[d] = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma**2)).astype(np.float32)
    return out


def _rmse(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sqrt(np.mean((a - b) ** 2)))


def _nse(observed: np.ndarray, predicted: np.ndarray) -> float:
    obs_mean = observed.mean()
    denom = float(np.sum((observed - obs_mean) ** 2))
    if denom == 0:
        return math.nan
    num = float(np.sum((predicted - observed) ** 2))
    return 1.0 - num / denom


def run_benchmark(seeds: int = 5, horizon: int = 7, epochs: int = 400) -> list[BenchmarkResult]:
    results: list[BenchmarkResult] = []
    rmses_pinn, rmses_persist, rmses_lagrangian, rmses_clim = [], [], [], []
    nse_pinn, nse_persist, nse_lagrangian, nse_clim = [], [], [], []

    for s in range(seeds):
        torch.manual_seed(s)
        ds = SyntheticDataset(n_obs=2000, seed=s)
        truth = _ground_truth_grid(ds, horizon, n=32)
        initial = truth[0]

        # Persistence
        pred_pers = PersistenceBaseline().predict_grid(initial, horizon_days=horizon)
        rmses_persist.append(_rmse(truth, pred_pers))
        nse_persist.append(_nse(truth, pred_pers))

        # Climatology — fit on the synthetic trajectory itself; this is an
        # "oracle climatology" which gives the fairest possible upper bound
        # for what a climatology forecast could ever achieve.
        clim = ClimatologyBaseline.fit(observations=truth)
        pred_clim = clim.predict_grid(initial_C=initial, horizon_days=horizon)
        rmses_clim.append(_rmse(truth, pred_clim))
        nse_clim.append(_nse(truth, pred_clim))

        # Lagrangian
        nx = truth.shape[2]
        pred_lag = LagrangianBaseline(
            alpha=0.03,
            K=ds.K_true,
            dt_seconds=1.0,
        ).predict_grid(
            initial_C=initial,
            u_ocean=np.full((nx, nx), ds.u_ocean * nx, dtype=np.float32),
            v_ocean=np.full((nx, nx), ds.v_ocean * nx, dtype=np.float32),
            u_wind=np.full((nx, nx), ds.u_wind * nx, dtype=np.float32),
            v_wind=np.full((nx, nx), ds.v_wind * nx, dtype=np.float32),
            horizon_days=horizon,
        )
        # Normalise so peak ~ initial peak
        if pred_lag.max() > 0:
            pred_lag = pred_lag * (initial.max() / pred_lag.max())
        rmses_lagrangian.append(_rmse(truth, pred_lag))
        nse_lagrangian.append(_nse(truth, pred_lag))

        # PINN
        model = PINN(hidden=64, depth=4, num_freq=4)
        cfg = TrainConfig(epochs=epochs, lr=1e-3, n_collocation=1024, n_obs_batch=512, device="cpu")
        model = train(model, ds, cfg, verbose=False)
        pred_pinn = _pinn_grid(model, horizon, n=32)
        rmses_pinn.append(_rmse(truth, pred_pinn))
        nse_pinn.append(_nse(truth, pred_pinn))

    for name, rmses, nses in (
        ("pinn", rmses_pinn, nse_pinn),
        ("persistence", rmses_persist, nse_persist),
        ("lagrangian", rmses_lagrangian, nse_lagrangian),
        ("climatology", rmses_clim, nse_clim),
    ):
        results.append(
            BenchmarkResult(
                model=name,
                horizon=horizon,
                rmse=float(np.mean(rmses)),
                nse=float(np.mean(nses)),
                seeds=seeds,
            )
        )
    return results


def _pinn_grid(model: PINN, horizon: int, n: int = 32) -> np.ndarray:
    model.eval()
    out = np.zeros((horizon, n, n), dtype=np.float32)
    grid = np.linspace(0, 1, n)
    with torch.no_grad():
        xx, yy = np.meshgrid(grid, grid)
        for d in range(horizon):
            t = torch.full((n * n,), d / 14.0)
            x = torch.tensor(xx.ravel(), dtype=torch.float32)
            y = torch.tensor(yy.ravel(), dtype=torch.float32)
            C = model(x, y, t).numpy().reshape(n, n)
            out[d] = np.clip(C, 0, None)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark PINN vs baselines")
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--horizon", type=int, default=7)
    parser.add_argument("--epochs", type=int, default=400)
    parser.add_argument(
        "--out",
        type=str,
        default="benchmarks/latest.json",
        help="Output JSON path (relative to apps/ml)",
    )
    args = parser.parse_args()

    results = run_benchmark(seeds=args.seeds, horizon=args.horizon, epochs=args.epochs)
    print(f"{'model':<14} {'rmse':>8} {'nse':>8} seeds={args.seeds}")
    for r in results:
        print(f"{r.model:<14} {r.rmse:>8.4f} {r.nse:>8.4f}")

    out = Path(__file__).resolve().parents[3] / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps([asdict(r) for r in results], indent=2))
    print(f"Saved to {out}")


if __name__ == "__main__":
    main()
