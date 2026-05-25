"""Unit tests for calibration helpers."""

from __future__ import annotations

import math

import numpy as np

from tideguard_ml.eval.calibration import (
    expected_calibration_error,
    reliability_diagram,
    temperature_scale,
)


def test_perfect_calibration_has_zero_ece() -> None:
    rng = np.random.default_rng(0)
    n = 10000
    p = rng.uniform(0, 1, n)
    y = (rng.uniform(0, 1, n) < p).astype(float)
    ece = expected_calibration_error(y, p, n_bins=10)
    assert ece < 0.03


def test_constant_overconfident_has_high_ece() -> None:
    rng = np.random.default_rng(0)
    n = 1000
    y = (rng.uniform(0, 1, n) < 0.5).astype(float)
    p = np.ones(n)  # always 1
    ece = expected_calibration_error(y, p, n_bins=10)
    # The model says always 1 but only half are 1 => ECE ~ 0.5.
    assert ece > 0.4


def test_reliability_diagram_bins_sum_to_n() -> None:
    rng = np.random.default_rng(1)
    n = 500
    p = rng.uniform(0, 1, n)
    y = (rng.uniform(0, 1, n) < p).astype(float)
    result = reliability_diagram(y, p, n_bins=10)
    assert int(result.bin_counts.sum()) == n
    assert result.bin_edges.shape == (11,)


def test_temperature_scaling_recovers_unity_for_calibrated() -> None:
    rng = np.random.default_rng(0)
    n = 5000
    logits = rng.normal(0, 1, n)
    p_true = 1.0 / (1.0 + np.exp(-logits))
    y = (rng.uniform(0, 1, n) < p_true).astype(float)
    T = temperature_scale(y, logits, n_iter=300, lr=0.1)
    assert math.isclose(T, 1.0, abs_tol=0.25)


def test_temperature_scaling_reduces_overconfidence() -> None:
    rng = np.random.default_rng(0)
    n = 5000
    logits_true = rng.normal(0, 1, n)
    p_true = 1.0 / (1.0 + np.exp(-logits_true))
    y = (rng.uniform(0, 1, n) < p_true).astype(float)
    # Overconfident model: doubles the logits.
    overconfident = 2.0 * logits_true
    T = temperature_scale(y, overconfident, n_iter=400, lr=0.1)
    # Optimal T should be ~ 2 to undo the doubling.
    assert 1.3 < T < 3.0
