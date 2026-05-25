"""Unit tests for probability-of-exceedance maps."""

from __future__ import annotations

import numpy as np
import pytest

from tideguard_ml.eval.exceedance import probability_of_exceedance


def test_uniform_ensemble_gives_constant_probability() -> None:
    arr = np.ones((5, 4, 4))
    result = probability_of_exceedance(arr, threshold=0.5)
    # Every member is 1.0 > 0.5 => p = 1 everywhere.
    assert np.allclose(result.probability, 1.0)


def test_threshold_above_max_gives_zero() -> None:
    arr = np.ones((5, 4, 4))
    result = probability_of_exceedance(arr, threshold=2.0)
    assert np.allclose(result.probability, 0.0)


def test_quantile_threshold_recovered() -> None:
    rng = np.random.default_rng(0)
    arr = rng.uniform(0, 1, (10, 6, 6))
    result = probability_of_exceedance(arr, quantile=0.9)
    assert 0.0 < result.threshold < 1.0
    # By construction ~10% of pixels-across-members exceed the q=0.9
    # threshold; per-pixel probability should be on average ~ 0.1.
    assert 0.0 <= result.probability.mean() <= 0.3


def test_requires_multiple_members() -> None:
    with pytest.raises(ValueError):
        probability_of_exceedance(np.ones((1, 4, 4)))
