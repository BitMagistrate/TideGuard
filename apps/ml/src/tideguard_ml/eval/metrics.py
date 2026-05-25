"""Scalar skill scores used in :mod:`tideguard_ml.eval.real_validation`.

Every function takes plain NumPy arrays and never touches torch, so the
same code path is reusable by the API service when it grades a daily
hindcast against citizen reports.

References
----------
- Nash, J.E., Sutcliffe, J.V. (1970). "River flow forecasting through
  conceptual models part I — A discussion of principles." Journal of
  Hydrology 10(3): 282-290.
- Brier, G.W. (1950). "Verification of forecasts expressed in terms of
  probability." Monthly Weather Review 78: 1-3.
"""

from __future__ import annotations

import math

import numpy as np


def rmse(observed: np.ndarray, predicted: np.ndarray) -> float:
    """Root-mean-square error. Lower is better."""
    observed = np.asarray(observed, dtype=np.float64)
    predicted = np.asarray(predicted, dtype=np.float64)
    if observed.shape != predicted.shape:
        raise ValueError(f"shape mismatch: {observed.shape} vs {predicted.shape}")
    return float(np.sqrt(np.mean((observed - predicted) ** 2)))


def mae(observed: np.ndarray, predicted: np.ndarray) -> float:
    """Mean absolute error. Lower is better."""
    observed = np.asarray(observed, dtype=np.float64)
    predicted = np.asarray(predicted, dtype=np.float64)
    if observed.shape != predicted.shape:
        raise ValueError(f"shape mismatch: {observed.shape} vs {predicted.shape}")
    return float(np.mean(np.abs(observed - predicted)))


def nse(observed: np.ndarray, predicted: np.ndarray) -> float:
    """Nash-Sutcliffe efficiency.

    1.0 = perfect, 0.0 = no better than predicting the observed mean,
    < 0 = worse than the observed mean (a strong signal to the jury that
    the model is *not* useful at this horizon).
    """
    observed = np.asarray(observed, dtype=np.float64)
    predicted = np.asarray(predicted, dtype=np.float64)
    if observed.shape != predicted.shape:
        raise ValueError(f"shape mismatch: {observed.shape} vs {predicted.shape}")
    obs_mean = float(observed.mean())
    denom = float(np.sum((observed - obs_mean) ** 2))
    if denom == 0:
        return math.nan
    num = float(np.sum((predicted - observed) ** 2))
    return 1.0 - num / denom


def brier_score(observed_binary: np.ndarray, predicted_prob: np.ndarray) -> float:
    """Brier score for binary forecasts. Lower is better; perfect = 0.

    ``observed_binary`` must be {0, 1}; ``predicted_prob`` must be in [0, 1].
    """
    observed_binary = np.asarray(observed_binary, dtype=np.float64)
    predicted_prob = np.asarray(predicted_prob, dtype=np.float64)
    if observed_binary.shape != predicted_prob.shape:
        raise ValueError(f"shape mismatch: {observed_binary.shape} vs {predicted_prob.shape}")
    if not np.all((observed_binary == 0) | (observed_binary == 1)):
        raise ValueError("observed_binary must contain only 0 or 1")
    return float(np.mean((predicted_prob - observed_binary) ** 2))


def roc_auc(observed_binary: np.ndarray, predicted_score: np.ndarray) -> float:
    """ROC-AUC via the Mann-Whitney U identity. No sklearn dependency.

    Returns NaN when only one class is present in ``observed_binary`` —
    the convention used by ``sklearn.metrics.roc_auc_score`` in the
    degenerate case.
    """
    observed_binary = np.asarray(observed_binary, dtype=np.float64)
    predicted_score = np.asarray(predicted_score, dtype=np.float64)
    if observed_binary.shape != predicted_score.shape:
        raise ValueError(f"shape mismatch: {observed_binary.shape} vs {predicted_score.shape}")
    positives = predicted_score[observed_binary == 1]
    negatives = predicted_score[observed_binary == 0]
    if positives.size == 0 or negatives.size == 0:
        return math.nan

    # Mann-Whitney U with mid-rank handling of ties.
    order = np.argsort(predicted_score, kind="mergesort")
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(1, len(predicted_score) + 1, dtype=np.float64)
    # Average ranks for ties.
    sorted_scores = predicted_score[order]
    i = 0
    while i < len(sorted_scores):
        j = i
        while j + 1 < len(sorted_scores) and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        if j > i:
            avg = (ranks[order[i]] + ranks[order[j]]) / 2.0
            ranks[order[i : j + 1]] = avg
        i = j + 1

    rank_sum_pos = float(np.sum(ranks[observed_binary == 1]))
    n_pos = float(positives.size)
    n_neg = float(negatives.size)
    auc = (rank_sum_pos - n_pos * (n_pos + 1.0) / 2.0) / (n_pos * n_neg)
    return float(auc)
