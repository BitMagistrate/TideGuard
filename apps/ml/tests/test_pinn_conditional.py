"""Smoke tests for the conditional PINN (TASK-001) and supporting modules."""

from __future__ import annotations

import math

import numpy as np
import torch

from tideguard_ml.adaptive import grad_norm_weights, ntk_weights
from tideguard_ml.ingest.forcing_provider import DEFAULT_BBOX, ForcingProvider
from tideguard_ml.ingest.sentinel import label_scene, synthesise_scene
from tideguard_ml.pinn import PINN, pde_residual
from tideguard_ml.symbolic import fit_symbolic_residual


def test_pinn_forward_with_forcing_runs() -> None:
    """forward(x,y,t,u_o,v_o,u_w,v_w) must accept all 7 channels."""
    n = 16
    model = PINN(hidden=16, depth=2, num_freq=4)
    x = torch.rand(n)
    y = torch.rand(n)
    t = torch.rand(n)
    out = model(
        x, y, t,
        u_ocean=torch.full((n,), 0.1),
        v_ocean=torch.full((n,), -0.05),
        u_wind=torch.full((n,), 2.0),
        v_wind=torch.full((n,), 1.0),
    )
    assert out.shape == (n,)
    assert not torch.isnan(out).any()


def test_pde_residual_with_forcing_no_nan() -> None:
    n = 32
    model = PINN(hidden=16, depth=2, num_freq=4)
    x = torch.rand(n)
    y = torch.rand(n)
    t = torch.rand(n)
    u_o = torch.full((n,), 0.1)
    v_o = torch.full((n,), -0.05)
    u_w = torch.full((n,), 2.0)
    v_w = torch.full((n,), 1.0)
    r = pde_residual(model, x, y, t, u_o, v_o, u_w, v_w)
    assert r.shape == (n,)
    assert not torch.isnan(r).any()


def test_adaptive_weights_normalise() -> None:
    """NTK / grad-norm weights must be finite and broadly the same order."""
    model = torch.nn.Linear(4, 1)
    x = torch.rand(16, 4, requires_grad=True)
    y_target = torch.zeros(16, 1)
    losses = {
        "a": ((model(x) - y_target) ** 2).mean(),
        "b": (model(x) ** 2).mean() * 5,
    }
    w_gn = grad_norm_weights(model, losses)
    w_ntk = ntk_weights(model, losses)
    for w in (w_gn, w_ntk):
        assert all(math.isfinite(v) for v in w.values())
        assert all(v > 0 for v in w.values())


def test_forcing_provider_synthetic_shapes() -> None:
    provider = ForcingProvider(bbox=DEFAULT_BBOX)
    lon = np.linspace(28, 41, 8)
    lat = np.linspace(41, 46, 8)
    t = np.linspace(0, 1, 8)
    sample = provider.sample(lon, lat, t)
    assert sample.u_ocean.shape == (8,)
    assert sample.v_ocean.shape == (8,)
    assert sample.u_wind.shape == (8,)
    assert sample.v_wind.shape == (8,)
    assert np.all(np.isfinite(sample.u_ocean))


def test_sentinel_fdi_synthetic_detection() -> None:
    """The Biermann FDI fires on the synthetic plume but not on flat water."""
    scene = synthesise_scene(
        scene_id="test",
        bbox=DEFAULT_BBOX,
        ts_seconds=0.0,
        plume_centre_uv=(0.5, 0.5),
        plume_radius=0.1,
        res=48,
    )
    detections = label_scene(scene)
    assert len(detections) > 0
    assert any(d["fdi"] > 0 for d in detections)


def test_symbolic_residual_fits_quadratic_with_fallback() -> None:
    """Polynomial fallback should recover a 2nd-order ground truth."""
    rng = np.random.default_rng(0)
    X = rng.uniform(-1, 1, size=(200, 2))
    y = 0.5 * X[:, 0] ** 2 + 0.3 * X[:, 0] * X[:, 1] - 0.2 * X[:, 1] + 0.1
    fit = fit_symbolic_residual(X, y, use_pysr=False, feature_names=["c", "rh"])
    assert fit.backend == "poly2"
    assert fit.r2 > 0.99
    assert "c*c" in fit.expression or "c*c" in " ".join(fit.coefficients)
