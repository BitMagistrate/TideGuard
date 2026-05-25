"""Unit tests for the climatology baseline."""

from __future__ import annotations

import numpy as np
import pytest

from tideguard_ml.baselines.climatology import ClimatologyBaseline


def test_fit_global_mean() -> None:
    obs = np.stack([np.full((4, 4), 0.2), np.full((4, 4), 0.4)])
    clim = ClimatologyBaseline.fit(obs)
    pred = clim.predict_grid(initial_C=None, horizon_days=3)
    assert pred.shape == (3, 4, 4)
    # All days should hold the global mean = 0.3.
    assert np.allclose(pred, 0.3, atol=1e-6)


def test_fit_monthly_means() -> None:
    obs = np.stack([np.full((2, 2), float(m)) for m in range(1, 13)])
    months = np.arange(1, 13)
    clim = ClimatologyBaseline.fit(obs, months=months)
    pred = clim.predict_grid(initial_C=None, horizon_days=3)
    # Within a 3-day horizon we stay inside one month bucket => prediction
    # equals the climatology for start_month.
    assert pred.shape == (3, 2, 2)


def test_predict_without_fit_requires_initial() -> None:
    clim = ClimatologyBaseline()
    with pytest.raises(ValueError):
        clim.predict_grid(initial_C=None, horizon_days=1)
    init = np.ones((3, 3), dtype=np.float32)
    out = clim.predict_grid(initial_C=init, horizon_days=2)
    assert out.shape == (2, 3, 3)
