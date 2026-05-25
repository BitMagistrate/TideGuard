"""Reliability diagram, expected calibration error and temperature scaling.

The juries we target (Stockholm Junior Water Prize, RELX) explicitly look
for calibrated uncertainty. A probabilistic forecast is calibrated when
the empirical frequency of an event in the subset of forecasts that gave
that event probability ``p`` is in fact close to ``p``.

This module implements:

- :func:`reliability_diagram`: bins forecasts by predicted probability and
  computes the observed event frequency in each bin (Murphy & Winkler
  1977).
- :func:`expected_calibration_error`: scalar ECE summary (Guo et al.
  2017).
- :func:`temperature_scale`: fits a single scalar ``T`` that minimises
  binary cross-entropy on a validation split — the cheapest post-hoc
  calibration trick and effective on ensembles (Guo et al. 2017, fig. 3).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class ECEResult:
    ece: float  # expected calibration error
    bin_edges: np.ndarray
    bin_counts: np.ndarray  # n forecasts per bin
    bin_observed: np.ndarray  # empirical frequency per bin
    bin_predicted: np.ndarray  # mean predicted probability per bin


def reliability_diagram(
    observed_binary: np.ndarray,
    predicted_prob: np.ndarray,
    n_bins: int = 10,
) -> ECEResult:
    """Compute reliability diagram bins + ECE on top of them.

    Args:
        observed_binary: 0/1 observation flags, shape ``(n,)``.
        predicted_prob: forecast probabilities in ``[0, 1]``, shape
            ``(n,)``.
        n_bins: equal-width bins in ``[0, 1]``.

    Returns:
        :class:`ECEResult` ready to be plotted with matplotlib.
    """
    observed_binary = np.asarray(observed_binary, dtype=np.float64)
    predicted_prob = np.asarray(predicted_prob, dtype=np.float64)
    if observed_binary.shape != predicted_prob.shape:
        raise ValueError(f"shape mismatch: {observed_binary.shape} vs {predicted_prob.shape}")
    if n_bins < 2:
        raise ValueError("n_bins must be >= 2")

    edges = np.linspace(0.0, 1.0, n_bins + 1)
    counts = np.zeros(n_bins, dtype=np.float64)
    observed = np.zeros(n_bins, dtype=np.float64)
    predicted = np.zeros(n_bins, dtype=np.float64)

    bin_idx = np.clip(np.searchsorted(edges, predicted_prob, side="right") - 1, 0, n_bins - 1)
    for b in range(n_bins):
        mask = bin_idx == b
        if not np.any(mask):
            continue
        counts[b] = float(np.sum(mask))
        observed[b] = float(np.mean(observed_binary[mask]))
        predicted[b] = float(np.mean(predicted_prob[mask]))

    n_total = float(observed_binary.size)
    ece = float(np.sum(counts / n_total * np.abs(observed - predicted)))
    return ECEResult(
        ece=ece,
        bin_edges=edges,
        bin_counts=counts,
        bin_observed=observed,
        bin_predicted=predicted,
    )


def expected_calibration_error(
    observed_binary: np.ndarray,
    predicted_prob: np.ndarray,
    n_bins: int = 10,
) -> float:
    """Convenience wrapper returning just the ECE scalar."""
    return reliability_diagram(observed_binary, predicted_prob, n_bins).ece


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def temperature_scale(
    observed_binary: np.ndarray,
    predicted_logits: np.ndarray,
    n_iter: int = 200,
    lr: float = 0.05,
) -> float:
    """Fit a single positive scalar ``T`` that minimises BCE.

    Returns the optimal ``T``; callers apply it as
    ``p_calibrated = sigmoid(logits / T)``.

    Uses log-space Adam-free gradient descent on the unconstrained
    ``s = log(T)`` parameter to keep ``T > 0`` without scipy.
    """
    observed_binary = np.asarray(observed_binary, dtype=np.float64)
    predicted_logits = np.asarray(predicted_logits, dtype=np.float64)
    if observed_binary.shape != predicted_logits.shape:
        raise ValueError(f"shape mismatch: {observed_binary.shape} vs {predicted_logits.shape}")

    s = 0.0  # log(T); start at T=1.
    for _ in range(n_iter):
        T = math.exp(s)
        scaled = predicted_logits / T
        p = 1.0 / (1.0 + np.exp(-scaled))
        # dL/dT = mean( (p - y) * (-logits / T^2) )
        grad_T = float(np.mean((p - observed_binary) * (-predicted_logits / (T * T))))
        # Chain rule for s = log T: dL/ds = dL/dT * T.
        grad_s = grad_T * T
        s -= lr * grad_s
    return float(math.exp(s))
