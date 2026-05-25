"""Probability-of-exceedance maps from a PINN deep ensemble.

A clean-up coordinator does not care about the *mean* concentration; they
need to know the *probability* that a given pixel will be in the top
``q``-quantile over the next ``H`` days. This module exposes a single
helper, :func:`probability_of_exceedance`, that converts a stack of
ensemble predictions into a probability map.

The same helper also returns the threshold used (in concentration units)
so the API can report it back to the client and so unit tests stay
deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ExceedanceMap:
    probability: np.ndarray  # shape (n_lat, n_lon), values in [0, 1]
    threshold: float  # concentration threshold (same units as the ensemble)
    quantile: float  # quantile used to pick the threshold
    n_members: int


def probability_of_exceedance(
    ensemble_predictions: np.ndarray,
    threshold: float | None = None,
    quantile: float = 0.9,
) -> ExceedanceMap:
    """Estimate per-pixel probability of exceeding a concentration threshold.

    Args:
        ensemble_predictions: shape ``(M, *spatial)`` with ``M`` ensemble
            members. Spatial dims are arbitrary (typically ``(n_lat, n_lon)``).
        threshold: concentration threshold. If ``None``, the global
            ``quantile`` of all values across all members is used (the
            "top 10% hotspot" convention used in TideGuard_WinPlan §1.6).
        quantile: only used when ``threshold is None``.

    Returns:
        :class:`ExceedanceMap`. The ``probability`` array has the same
        spatial shape as a single ensemble member and gives the fraction
        of members whose value at that pixel exceeded ``threshold``.
    """
    arr = np.asarray(ensemble_predictions, dtype=np.float64)
    if arr.ndim < 2:
        raise ValueError(f"ensemble_predictions must have shape (M, *spatial); got {arr.shape}")
    if arr.shape[0] < 2:
        raise ValueError("Need at least 2 ensemble members to compute exceedance probability")
    if not (0.0 < quantile < 1.0):
        raise ValueError("quantile must be in (0, 1)")

    if threshold is None:
        threshold = float(np.quantile(arr, quantile))

    above = (arr > threshold).astype(np.float64)
    prob = above.mean(axis=0)
    return ExceedanceMap(
        probability=prob,
        threshold=float(threshold),
        quantile=float(quantile),
        n_members=int(arr.shape[0]),
    )
