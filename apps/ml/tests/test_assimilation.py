"""Unit tests for the EnKF on the chaotic Lorenz-63 system."""

from __future__ import annotations

import numpy as np

from tideguard_ml.assimilation import (
    EnKFConfig,
    EnsembleKalmanFilter,
    lorenz63,
)


def _truth_trajectory(steps: int, dt: float = 0.01) -> np.ndarray:
    s = np.array([1.0, 1.0, 1.0])
    out = np.zeros((steps, 3))
    for k in range(steps):
        s = lorenz63(s, dt=dt, steps=1)
        out[k] = s
    return out


def test_enkf_tracks_lorenz63() -> None:
    rng = np.random.default_rng(42)
    n_state = 3
    n_members = 64

    # Random ensemble centred on the wrong initial condition.
    ic_perturbed = np.array([1.0, 1.0, 1.0]) + rng.normal(scale=2.0, size=3)
    ensemble = ic_perturbed[:, None] + rng.normal(scale=1.0, size=(n_state, n_members))

    enkf = EnsembleKalmanFilter(
        ensemble=ensemble,
        config=EnKFConfig(n_members=n_members, inflation=1.02),
        rng=rng,
    )

    truth = _truth_trajectory(steps=200)
    H = np.eye(n_state)
    R = 0.5 * np.eye(n_state)

    # Run the filter, assimilating every 5 steps.
    estimated = np.zeros_like(truth)
    for k in range(truth.shape[0]):
        # Forecast: each member propagates one Lorenz step.
        enkf.forecast(lambda s: lorenz63(s, steps=1))
        if k % 5 == 4:
            obs = truth[k] + rng.normal(scale=np.sqrt(0.5), size=3)
            enkf.update(obs, H, R)
        estimated[k] = enkf.state

    # After the spin-up the analysis should track the truth.
    rmse = np.sqrt(np.mean((estimated[50:] - truth[50:]) ** 2))
    no_da = ic_perturbed - truth[50:]
    rmse_no_da = np.sqrt(np.mean(no_da ** 2))
    assert rmse < rmse_no_da, (
        f"EnKF did not improve over no-DA: rmse={rmse:.2f} vs {rmse_no_da:.2f}"
    )
    assert rmse < 3.0, f"EnKF rmse {rmse:.2f} too high"
