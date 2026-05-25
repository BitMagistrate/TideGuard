"""Tests for PINN model and synthetic training."""

from __future__ import annotations

import torch

from tideguard_ml.data import SyntheticDataset
from tideguard_ml.pinn import PINN, pde_residual
from tideguard_ml.train import TrainConfig, train


def test_pinn_forward_shape() -> None:
    model = PINN(hidden=32, depth=2, num_freq=4)
    x = torch.rand(16)
    y = torch.rand(16)
    t = torch.rand(16)
    out = model(x, y, t)
    assert out.shape == (16,)


def test_pinn_learnable_params_positive() -> None:
    model = PINN()
    assert model.alpha.item() > 0
    assert model.K.item() > 0
    assert model.lam.item() > 0


def test_pde_residual_no_nan() -> None:
    model = PINN(hidden=32, depth=2, num_freq=4)
    n = 16
    x = torch.rand(n)
    y = torch.rand(n)
    t = torch.rand(n)
    u_o = torch.full((n,), 0.2)
    v_o = torch.full((n,), 0.1)
    u_w = torch.full((n,), 1.0)
    v_w = torch.full((n,), 0.5)
    r = pde_residual(model, x, y, t, u_o, v_o, u_w, v_w)
    assert not torch.isnan(r).any()
    assert r.shape == (n,)


def test_synthetic_dataset_sampling() -> None:
    ds = SyntheticDataset(n_obs=100, seed=42)
    obs = ds.sample_obs(32)
    assert obs.x.shape == (32,)
    assert obs.y.shape == (32,)
    assert obs.t.shape == (32,)
    assert obs.C.shape == (32,)
    col = ds.sample_collocation(64)
    assert col.x.shape == (64,)


def test_training_smoke_run() -> None:
    """Smoke test: train for a few steps, ensure loss decreases."""
    torch.manual_seed(42)
    ds = SyntheticDataset(n_obs=500, seed=42)
    model = PINN(hidden=32, depth=2, num_freq=4)
    cfg = TrainConfig(
        epochs=30,
        lr=1e-3,
        n_collocation=128,
        n_obs_batch=64,
    )

    initial_loss = None
    final_loss = None

    opt = torch.optim.Adam(model.parameters(), lr=cfg.lr)
    for step in range(cfg.epochs):
        opt.zero_grad()
        obs = ds.sample_obs(cfg.n_obs_batch)
        C_pred = model(obs.x, obs.y, obs.t)
        loss_data = ((C_pred - obs.C) ** 2).mean()
        col = ds.sample_collocation(cfg.n_collocation)
        r = pde_residual(model, col.x, col.y, col.t, col.u_o, col.v_o, col.u_w, col.v_w)
        loss_pde = (r**2).mean()
        loss = loss_data + 0.01 * loss_pde
        loss.backward()
        opt.step()
        if step == 0:
            initial_loss = loss.item()
        final_loss = loss.item()

    assert final_loss is not None and initial_loss is not None
    assert final_loss < initial_loss, f"Loss did not decrease: {initial_loss} -> {final_loss}"


def test_train_function_runs() -> None:
    torch.manual_seed(42)
    ds = SyntheticDataset(n_obs=300, seed=42)
    model = PINN(hidden=16, depth=2, num_freq=4)
    cfg = TrainConfig(epochs=5, lr=1e-3, n_collocation=64, n_obs_batch=32)
    trained = train(model, ds, cfg)
    assert trained is model
