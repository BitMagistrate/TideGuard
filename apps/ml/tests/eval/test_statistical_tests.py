"""Unit tests for the Diebold-Mariano and bootstrap CI helpers."""

from __future__ import annotations

import numpy as np
import pytest

from tideguard_ml.eval.statistical_tests import bootstrap_rmse_ci, diebold_mariano


def test_dm_detects_significant_difference() -> None:
    rng = np.random.default_rng(0)
    n = 500
    # Model A is worse — its losses are larger by a constant.
    loss_b = rng.uniform(0, 1, n)
    loss_a = loss_b + 0.2
    result = diebold_mariano(loss_a, loss_b)
    assert result.p_value < 0.01
    assert result.sign == 1
    assert result.n == n


def test_dm_no_difference_high_p_value() -> None:
    rng = np.random.default_rng(0)
    loss = rng.uniform(0, 1, 500)
    result = diebold_mariano(loss, loss + 1e-9)
    assert result.p_value > 0.05


def test_dm_rejects_short_input() -> None:
    with pytest.raises(ValueError):
        diebold_mariano(np.array([0.1, 0.2]), np.array([0.3, 0.4]))


def test_bootstrap_ci_contains_zero_when_models_match() -> None:
    rng = np.random.default_rng(1)
    observed = rng.uniform(0, 1, 200)
    pred_a = observed + rng.normal(0, 0.05, 200)
    pred_b = observed + rng.normal(0, 0.05, 200)
    result = bootstrap_rmse_ci(observed, pred_a, pred_b, n_replicates=300, seed=42)
    # When both models have ~equal skill, the CI should straddle zero.
    assert result.ci_low <= 0 <= result.ci_high


def test_bootstrap_ci_excludes_zero_when_models_differ() -> None:
    rng = np.random.default_rng(2)
    observed = rng.uniform(0, 1, 500)
    pred_a = np.full_like(observed, 0.5)  # constant — large error
    pred_b = observed + rng.normal(0, 0.01, 500)  # tight
    result = bootstrap_rmse_ci(observed, pred_a, pred_b, n_replicates=500, seed=7)
    # A is much worse than B => delta_mean > 0 and CI excludes zero.
    assert result.delta_mean > 0
    assert result.ci_low > 0
