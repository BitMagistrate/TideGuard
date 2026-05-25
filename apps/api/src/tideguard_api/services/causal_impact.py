"""Synthetic-control causal-impact estimator (P1-12).

The service implements a lightweight version of Brodersen et al.
"Inferring causal impact using Bayesian structural time-series models"
(Annals of Applied Statistics, 2015) — we forecast the
counterfactual post-intervention trajectory by fitting a weighted
combination of donor regions on the *pre*-intervention window, then
the impact is ``treated_post - counterfactual_post``.

The implementation deliberately uses only NumPy so it remains
dependency-light.  It is exposed via the ``/impact/causal`` route in
``routers/impact.py`` and consumed by the public Impact dashboard.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass
class CausalImpactResult:
    counterfactual: np.ndarray
    actual: np.ndarray
    impact: np.ndarray
    cumulative_impact: float
    relative_effect: float
    donor_weights: np.ndarray
    pre_rmse: float

    def to_dict(self) -> dict:
        return {
            "counterfactual": self.counterfactual.tolist(),
            "actual": self.actual.tolist(),
            "impact": self.impact.tolist(),
            "cumulative_impact": float(self.cumulative_impact),
            "relative_effect": float(self.relative_effect),
            "donor_weights": self.donor_weights.tolist(),
            "pre_rmse": float(self.pre_rmse),
        }


def _solve_simplex_weights(X_pre: np.ndarray, y_pre: np.ndarray) -> np.ndarray:
    """Solve ``min ||X_pre @ w - y_pre|| s.t. w >= 0, sum(w) = 1``.

    We use a projected-gradient descent on the simplex.  Small problem
    sizes (~10 donors, ~100 timesteps) converge in well under a second.
    """
    n_donors = X_pre.shape[1]
    w = np.full(n_donors, 1.0 / n_donors)
    lr = 0.1 / max(1.0, float(np.linalg.norm(X_pre, ord=2)) ** 2)

    for _ in range(2_000):
        residual = X_pre @ w - y_pre
        grad = X_pre.T @ residual
        w = w - lr * grad
        # Project onto the unit simplex (Wang & Carreira-Perpiñán 2013).
        u = np.sort(w)[::-1]
        cssv = np.cumsum(u) - 1.0
        rho = np.where(u - cssv / (np.arange(n_donors) + 1) > 0)[0]
        if rho.size == 0:
            w = np.zeros_like(w)
            w[0] = 1.0
            continue
        theta = cssv[rho[-1]] / (rho[-1] + 1)
        w = np.maximum(w - theta, 0.0)
    return w


def causal_impact(
    treated: Sequence[float],
    donors: Sequence[Sequence[float]],
    intervention_index: int,
) -> CausalImpactResult:
    """Estimate the causal effect of the intervention on the treated series.

    ``donors`` is a list of donor time series, each of the same length
    as ``treated``.  ``intervention_index`` is the first index in the
    *post-intervention* window.
    """
    y = np.asarray(treated, dtype=float)
    X = np.asarray(donors, dtype=float).T  # (T, n_donors)
    if X.ndim == 1:
        X = X[:, None]
    if y.shape[0] != X.shape[0]:
        raise ValueError("treated and donors must be the same length")
    if intervention_index <= 1 or intervention_index >= y.shape[0]:
        raise ValueError("intervention_index out of range")

    X_pre, y_pre = X[:intervention_index], y[:intervention_index]
    weights = _solve_simplex_weights(X_pre, y_pre)
    counterfactual = X @ weights
    pre_rmse = float(np.sqrt(np.mean((counterfactual[:intervention_index] - y_pre) ** 2)))

    actual = y.copy()
    impact = actual - counterfactual
    cumulative = float(np.sum(impact[intervention_index:]))
    base = float(np.sum(counterfactual[intervention_index:])) or 1.0
    relative = cumulative / base
    return CausalImpactResult(
        counterfactual=counterfactual,
        actual=actual,
        impact=impact,
        cumulative_impact=cumulative,
        relative_effect=relative,
        donor_weights=weights,
        pre_rmse=pre_rmse,
    )


__all__ = ["CausalImpactResult", "causal_impact"]
