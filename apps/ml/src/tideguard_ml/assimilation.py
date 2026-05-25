"""Ensemble Kalman Filter (EnKF) for state-space data assimilation.

The EnKF approximates the Kalman filter for nonlinear state-space
models by representing the prior covariance as a Monte-Carlo ensemble.
See Evensen (2003) `The Ensemble Kalman Filter`, Ocean Dyn. 53.

The implementation is deliberately minimal:

* ``EnsembleKalmanFilter.forecast(f)`` applies a user-supplied
  state-transition function ``f(state) -> state`` to each ensemble
  member (additive process noise can be folded into ``f``).
* ``EnsembleKalmanFilter.update(y, H, R)`` ingests observation ``y``
  with linear observation operator ``H`` and observation covariance
  ``R``.  Localisation/inflation are out of scope (the audit asks for
  a baseline EnKF + Lorenz unit test).

The class is unit-tested against the chaotic Lorenz-63 system; see
``tests/test_assimilation.py`` for the regression test.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


@dataclass
class EnKFConfig:
    n_members: int = 64
    inflation: float = 1.0


class EnsembleKalmanFilter:
    def __init__(
        self,
        ensemble: np.ndarray,
        config: EnKFConfig | None = None,
        rng: np.random.Generator | None = None,
    ) -> None:
        if ensemble.ndim != 2:
            raise ValueError("ensemble must be 2-D: (n_state, n_members)")
        self.ensemble = ensemble.astype(np.float64)
        self.config = config or EnKFConfig(n_members=ensemble.shape[1])
        self.rng = rng or np.random.default_rng(0)

    @property
    def state(self) -> np.ndarray:
        return self.ensemble.mean(axis=1)

    @property
    def n_state(self) -> int:
        return self.ensemble.shape[0]

    @property
    def n_members(self) -> int:
        return self.ensemble.shape[1]

    def forecast(self, propagate: Callable[[np.ndarray], np.ndarray]) -> None:
        """Apply ``propagate`` to each ensemble column in place."""
        new = np.empty_like(self.ensemble)
        for m in range(self.n_members):
            new[:, m] = propagate(self.ensemble[:, m])
        self.ensemble = new
        if self.config.inflation > 1.0:
            mean = self.ensemble.mean(axis=1, keepdims=True)
            self.ensemble = mean + self.config.inflation * (self.ensemble - mean)

    def update(
        self,
        observation: np.ndarray,
        H: np.ndarray,
        R: np.ndarray,
    ) -> None:
        """Apply the standard stochastic EnKF analysis step.

        ``H`` maps state to observation space, shape ``(n_obs, n_state)``.
        ``R`` is the observation covariance, shape ``(n_obs, n_obs)``.
        """
        if H.shape[1] != self.n_state:
            raise ValueError("H has wrong number of columns")
        if observation.ndim != 1 or observation.shape[0] != H.shape[0]:
            raise ValueError("observation shape must match H rows")

        x_mean = self.ensemble.mean(axis=1, keepdims=True)
        anomalies = self.ensemble - x_mean
        # Sample covariance: A A^T / (m-1)
        P = anomalies @ anomalies.T / max(self.n_members - 1, 1)
        S = H @ P @ H.T + R
        K = P @ H.T @ np.linalg.pinv(S)

        # Stochastic perturbed-obs update: add per-member observation noise.
        noise = self.rng.multivariate_normal(
            mean=np.zeros(observation.shape[0]),
            cov=R,
            size=self.n_members,
        ).T
        innov = observation[:, None] + noise - H @ self.ensemble
        self.ensemble = self.ensemble + K @ innov


def lorenz63(state: np.ndarray, dt: float = 0.01, sigma: float = 10.0,
             beta: float = 8.0 / 3.0, rho: float = 28.0,
             steps: int = 1) -> np.ndarray:
    """Integrate the canonical Lorenz-63 system with RK4."""
    x, y, z = state
    for _ in range(steps):
        def deriv(s: np.ndarray) -> np.ndarray:
            xx, yy, zz = s
            return np.array(
                [sigma * (yy - xx), xx * (rho - zz) - yy, xx * yy - beta * zz]
            )

        k1 = deriv(np.array([x, y, z]))
        k2 = deriv(np.array([x, y, z]) + 0.5 * dt * k1)
        k3 = deriv(np.array([x, y, z]) + 0.5 * dt * k2)
        k4 = deriv(np.array([x, y, z]) + dt * k3)
        x, y, z = (np.array([x, y, z]) + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0).tolist()
    return np.array([x, y, z])


__all__ = [
    "EnKFConfig",
    "EnsembleKalmanFilter",
    "lorenz63",
]
