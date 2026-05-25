"""Smoke test for the real-data validation harness.

We train a tiny PINN on the synthetic dataset, save the checkpoint,
synthesise a small CSV that *should* roughly match it, then run
``run_validation`` end-to-end and check that the resulting report is
well-formed.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import torch

from tideguard_ml.data import SyntheticDataset
from tideguard_ml.eval.real_validation import _parse_bbox, run_validation
from tideguard_ml.pinn import PINN
from tideguard_ml.train import TrainConfig, train


def _train_tiny_pinn(tmp_path: Path) -> Path:
    torch.manual_seed(0)
    model = PINN(hidden=32, depth=3, num_freq=4)
    ds = SyntheticDataset(n_obs=500, seed=0)
    cfg = TrainConfig(epochs=80, lr=2e-3, n_collocation=128, n_obs_batch=128, device="cpu")
    model = train(model, ds, cfg, verbose=False)
    ckpt = tmp_path / "tiny.pt"
    torch.save({"model_state_dict": model.state_dict()}, ckpt)
    return ckpt


def _make_csv(tmp_path: Path, n: int = 60) -> Path:
    rng = np.random.default_rng(0)
    rows = []
    for _ in range(n):
        lon = float(rng.uniform(30, 40))
        lat = float(rng.uniform(42, 45))
        ts = float(rng.uniform(0, 1) * 86400 * 30)
        c = float(np.clip(rng.normal(0.3, 0.15), 0, 1))
        rows.append({"lon": lon, "lat": lat, "ts_seconds": ts, "concentration": c})
    path = tmp_path / "obs.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["lon", "lat", "ts_seconds", "concentration"])
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_real_validation_round_trip(tmp_path: Path) -> None:
    pytest_pandas = __import__("importlib").util.find_spec("pandas")
    if pytest_pandas is None:  # pragma: no cover
        import pytest

        pytest.skip("pandas not installed")

    csv_path = _make_csv(tmp_path)
    ckpt = _train_tiny_pinn(tmp_path)
    report = run_validation(
        csv=csv_path,
        checkpoint=ckpt,
        bbox=(27.0, 40.0, 42.0, 47.0),
        threshold_quantile=0.9,
        bootstrap_replicates=80,
    )
    assert report.n_observations > 0
    assert set(report.metrics) == {"pinn", "persistence", "climatology"}
    for model_metrics in report.metrics.values():
        assert "rmse" in model_metrics
        assert "mae" in model_metrics
        assert "nse" in model_metrics
        assert "brier" in model_metrics
    # JSON round-trips cleanly.
    payload = json.dumps(report.metrics)
    assert isinstance(payload, str)


def test_parse_bbox() -> None:
    assert _parse_bbox("27,40,42,47") == (27.0, 40.0, 42.0, 47.0)
