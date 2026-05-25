"""Tests for the ensemble / UQ helpers."""

from __future__ import annotations

from tideguard_ml.uq import carbon_estimate


def test_carbon_estimate_positive():
    assert carbon_estimate(epochs=100, n_params=100_000) > 0


def test_carbon_estimate_scales_with_epochs():
    a = carbon_estimate(epochs=100, n_params=100_000)
    b = carbon_estimate(epochs=1000, n_params=100_000)
    assert b > a
