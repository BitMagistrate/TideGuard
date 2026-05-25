"""Tests for the persistence + Lagrangian baselines."""

from __future__ import annotations

import numpy as np

from tideguard_ml.baselines.lagrangian import LagrangianBaseline
from tideguard_ml.baselines.persistence import PersistenceBaseline


def test_persistence_returns_constant_horizon():
    initial = np.random.rand(8, 8).astype(np.float32)
    pred = PersistenceBaseline().predict_grid(initial, horizon_days=5)
    assert pred.shape == (5, 8, 8)
    # Every day is the initial field
    for d in range(5):
        assert np.allclose(pred[d], initial)


def test_lagrangian_predicts_horizon():
    initial = np.zeros((16, 16), dtype=np.float32)
    initial[8, 8] = 1.0
    pred = LagrangianBaseline(alpha=0.0, K=1e-4, n_particles=1000, seed=0).predict_grid(
        initial_C=initial,
        u_ocean=np.zeros((16, 16), dtype=np.float32),
        v_ocean=np.zeros((16, 16), dtype=np.float32),
        u_wind=np.zeros((16, 16), dtype=np.float32),
        v_wind=np.zeros((16, 16), dtype=np.float32),
        horizon_days=3,
    )
    assert pred.shape == (3, 16, 16)
    # Density is a probability distribution per day
    for d in range(3):
        assert pred[d].sum() > 0
