"""Unit tests for tideguard_ml.eval.metrics."""

from __future__ import annotations

import math

import numpy as np
import pytest

from tideguard_ml.eval.metrics import brier_score, mae, nse, rmse, roc_auc


def test_rmse_zero_when_equal() -> None:
    a = np.array([0.1, 0.2, 0.3])
    assert rmse(a, a) == 0.0


def test_rmse_known_value() -> None:
    observed = np.array([1.0, 2.0, 3.0])
    predicted = np.array([0.0, 0.0, 0.0])
    expected = math.sqrt((1 + 4 + 9) / 3)
    assert rmse(observed, predicted) == pytest.approx(expected)


def test_mae_known_value() -> None:
    observed = np.array([1.0, 2.0, 3.0])
    predicted = np.array([0.0, 1.0, 5.0])
    assert mae(observed, predicted) == pytest.approx((1 + 1 + 2) / 3)


def test_nse_perfect() -> None:
    observed = np.array([1.0, 2.0, 3.0, 4.0])
    assert nse(observed, observed) == pytest.approx(1.0)


def test_nse_predicting_mean_gives_zero() -> None:
    observed = np.array([1.0, 2.0, 3.0, 4.0])
    predicted = np.full_like(observed, observed.mean())
    assert nse(observed, predicted) == pytest.approx(0.0, abs=1e-9)


def test_brier_zero_for_perfect() -> None:
    y = np.array([0, 1, 1, 0])
    p = np.array([0.0, 1.0, 1.0, 0.0])
    assert brier_score(y, p) == 0.0


def test_brier_invalid_observed_raises() -> None:
    with pytest.raises(ValueError):
        brier_score(np.array([0, 1, 2]), np.array([0.1, 0.2, 0.3]))


def test_roc_auc_perfect_separation() -> None:
    y = np.array([0, 0, 1, 1])
    s = np.array([0.1, 0.2, 0.8, 0.9])
    assert roc_auc(y, s) == pytest.approx(1.0)


def test_roc_auc_random_is_half() -> None:
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 2000)
    s = rng.uniform(0, 1, 2000)
    assert abs(roc_auc(y, s) - 0.5) < 0.05


def test_roc_auc_returns_nan_for_single_class() -> None:
    y = np.zeros(5)
    s = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    assert math.isnan(roc_auc(y, s))


def test_shape_mismatch_raises() -> None:
    with pytest.raises(ValueError):
        rmse(np.array([0.0]), np.array([0.0, 1.0]))
