"""Statistical significance tests for forecast comparisons.

The plan we are executing against (see ``docs/research_paper.md`` §3.4 and
``TideGuard_WinPlan.md`` §1.4) requires every public claim of the form
"PINN beats baseline X" to be backed by both a Diebold-Mariano test and a
bootstrap 95% confidence interval on the difference of RMSE. This module
implements both with no extra dependencies beyond NumPy.

Both functions take ``loss_a`` and ``loss_b`` arrays of *pointwise*
squared (or absolute) errors evaluated on the same observations; they
return ``(statistic, p_value, ci_low, ci_high)`` tuples for direct
interpolation into the paper.

References
----------
- Diebold, F.X., Mariano, R.S. (1995). "Comparing predictive accuracy."
  Journal of Business & Economic Statistics 13(3): 253-263.
- Harvey, D., Leybourne, S., Newbold, P. (1997). "Testing the equality of
  prediction mean squared errors." International Journal of Forecasting
  13(2): 281-291.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# Standard-normal CDF in pure NumPy (avoids the scipy dependency).
_SQRT2 = math.sqrt(2.0)


def _norm_sf(x: float) -> float:
    """Standard-normal survival function P(Z > x)."""
    return 0.5 * math.erfc(x / _SQRT2)


@dataclass
class DMResult:
    statistic: float  # DM test statistic (Z-score under H0)
    p_value: float  # two-sided p-value
    n: int  # sample size used
    sign: int  # +1 if loss_a > loss_b on average, -1 otherwise


def diebold_mariano(
    loss_a: np.ndarray,
    loss_b: np.ndarray,
    h: int = 1,
    harvey_adjustment: bool = True,
) -> DMResult:
    """Two-sided Diebold-Mariano test on paired loss differentials.

    Args:
        loss_a, loss_b: pointwise loss values evaluated on the same
            observations, shape ``(n,)``. Lower means better.
        h: forecast horizon in *steps*; controls the Newey-West truncation
            (``h - 1``).
        harvey_adjustment: if True, apply the small-sample correction of
            Harvey, Leybourne & Newbold (1997). Recommended for ``n < 50``.

    Returns:
        :class:`DMResult` with the statistic, two-sided p-value, sample
        size used, and the sign of ``mean(loss_a - loss_b)``.

    A two-sided p-value below 0.05 means the difference in forecast
    accuracy is statistically significant at the 5% level; the ``sign``
    field tells you which model is better (``+1`` => loss_a worse => model
    B is better; ``-1`` => loss_b worse => model A is better).
    """
    loss_a = np.asarray(loss_a, dtype=np.float64)
    loss_b = np.asarray(loss_b, dtype=np.float64)
    if loss_a.shape != loss_b.shape:
        raise ValueError(f"shape mismatch: {loss_a.shape} vs {loss_b.shape}")
    mask = np.isfinite(loss_a) & np.isfinite(loss_b)
    d = (loss_a - loss_b)[mask]
    n = int(d.size)
    if n < 4:
        raise ValueError("DM test needs at least 4 paired finite observations")

    d_mean = float(d.mean())
    # Newey-West HAC variance with Bartlett kernel, truncation h-1.
    variances = [float(np.mean((d - d_mean) ** 2))]
    for lag in range(1, min(h, n)):
        cov = float(np.mean((d[lag:] - d_mean) * (d[:-lag] - d_mean)))
        weight = 1.0 - lag / h
        variances.append(2.0 * weight * cov)
    long_run_var = max(sum(variances), 1e-12) / n
    dm = d_mean / math.sqrt(long_run_var)

    if harvey_adjustment:
        # Harvey/Leybourne/Newbold small-sample correction.
        adj = math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
        dm = dm * adj

    p_two_sided = 2.0 * _norm_sf(abs(dm))
    sign = 1 if d_mean > 0 else (-1 if d_mean < 0 else 0)
    return DMResult(statistic=float(dm), p_value=float(p_two_sided), n=n, sign=sign)


@dataclass
class BootstrapCI:
    delta_mean: float  # mean RMSE(model A) - RMSE(model B)
    ci_low: float
    ci_high: float
    n_replicates: int
    confidence: float


def bootstrap_rmse_ci(
    observed: np.ndarray,
    predicted_a: np.ndarray,
    predicted_b: np.ndarray,
    n_replicates: int = 1000,
    confidence: float = 0.95,
    seed: int = 0,
) -> BootstrapCI:
    """Percentile-bootstrap CI on ``RMSE(A) - RMSE(B)``.

    The CI is computed by re-sampling observation indices with replacement
    ``n_replicates`` times and recomputing the RMSE difference each time;
    the empirical ``[(1-c)/2, 1-(1-c)/2]`` percentiles are returned.

    If the resulting interval does not cross zero, the difference is
    statistically significant at level ``1 - confidence`` (Wasserman 2004,
    §8.3).
    """
    observed = np.asarray(observed, dtype=np.float64)
    predicted_a = np.asarray(predicted_a, dtype=np.float64)
    predicted_b = np.asarray(predicted_b, dtype=np.float64)
    if not (observed.shape == predicted_a.shape == predicted_b.shape):
        raise ValueError("observed, predicted_a, predicted_b must share shape")
    n = int(observed.size)
    if n < 4:
        raise ValueError("bootstrap needs at least 4 observations")

    rng = np.random.default_rng(seed)
    obs_flat = observed.ravel()
    a_flat = predicted_a.ravel()
    b_flat = predicted_b.ravel()
    deltas = np.empty(n_replicates, dtype=np.float64)
    for i in range(n_replicates):
        idx = rng.integers(0, n, n)
        rmse_a = math.sqrt(float(np.mean((obs_flat[idx] - a_flat[idx]) ** 2)))
        rmse_b = math.sqrt(float(np.mean((obs_flat[idx] - b_flat[idx]) ** 2)))
        deltas[i] = rmse_a - rmse_b

    alpha = (1.0 - confidence) / 2.0
    ci_low = float(np.quantile(deltas, alpha))
    ci_high = float(np.quantile(deltas, 1.0 - alpha))
    delta_mean = float(
        math.sqrt(float(np.mean((obs_flat - a_flat) ** 2))) - math.sqrt(float(np.mean((obs_flat - b_flat) ** 2)))
    )
    return BootstrapCI(
        delta_mean=delta_mean,
        ci_low=ci_low,
        ci_high=ci_high,
        n_replicates=int(n_replicates),
        confidence=float(confidence),
    )
