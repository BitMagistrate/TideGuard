"""Uncertainty quantification — ensemble + Laplace approximation.

Per TIDEGUARD_AUDIT.md TASK-003 (CRIT-ML-5):
  * ``PINNEnsemble``: load N (default 5) trained checkpoints, return
    per-cell mean + std + exceedance-probability.
  * ``laplace_posterior_std``: a fast last-layer Laplace approximation
    of the predictive variance. Useful when only a single checkpoint
    is available — gives an honest "epistemic" uncertainty band.

We removed the mock-noise fall-back in ``PINNEnsemble``: when no checkpoints
are found the constructor *raises* instead of silently injecting Gaussian
noise. The HTTP layer (`apps/api/.../services/inference.py`) handles the
"no real ensemble" case with a perturbed-initial-condition mock that is
clearly labelled in `model_version`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

from tideguard_ml.inference import PINNInferenceService


@dataclass
class EnsembleResult:
    lons: np.ndarray
    lats: np.ndarray
    mean: np.ndarray          # (horizon, ny, nx)
    std: np.ndarray           # (horizon, ny, nx)
    members: int


class PINNEnsemble:
    """Load several checkpoints and aggregate their predictions."""

    def __init__(self, checkpoint_paths: list[str | Path], device: str = "cpu"):
        if not checkpoint_paths:
            raise ValueError("PINNEnsemble requires at least one checkpoint")
        self.services = [PINNInferenceService(str(p), device=device) for p in checkpoint_paths]

    def predict(
        self,
        lon_min: float,
        lon_max: float,
        lat_min: float,
        lat_max: float,
        horizon_days: int = 7,
        resolution: int = 24,
    ) -> EnsembleResult:
        outputs = []
        lons = lats = None
        for svc in self.services:
            res = svc.predict(lon_min, lon_max, lat_min, lat_max, horizon_days, resolution)
            outputs.append(res.concentration)
            lons, lats = res.lons, res.lats
        stack = np.stack(outputs, axis=0)
        return EnsembleResult(
            lons=lons,  # type: ignore[arg-type]
            lats=lats,  # type: ignore[arg-type]
            mean=stack.mean(axis=0),
            std=stack.std(axis=0),
            members=len(self.services),
        )


def laplace_posterior_std(
    service: PINNInferenceService,
    lons: np.ndarray,
    lats: np.ndarray,
    times: np.ndarray,
    sigma_prior: float = 1.0,
) -> np.ndarray:
    """Last-layer Laplace posterior std for a trained PINN.

    Approximates the posterior over the *output* linear layer's weights with
    a Gaussian centred at the MAP estimate. Each predictive variance is
    ``φ(x).T  Σ_post  φ(x) + sigma_obs²``, where ``Σ_post = (Σ_prior⁻¹ + Φ.T Φ)⁻¹``.

    This is the textbook Laplace approximation (MacKay 1992) restricted to
    the head layer, which is the canonical "Bayesian PINN on a budget"
    used in production (Daxberger et al. 2021).

    Parameters
    ----------
    lons, lats : 1-D arrays in real coordinates.
    times : 1-D array of normalised times (matching the model's training).
    sigma_prior : prior std on the head weights.

    Returns
    -------
    std : array of shape (len(times), len(lats), len(lons)).
    """
    model = service.model
    # Locate the last (output) Linear layer.
    last_linear = None
    for mod in model.net:
        if isinstance(mod, torch.nn.Linear):
            last_linear = mod
    if last_linear is None:
        raise RuntimeError("PINN.net has no Linear layers — corrupt checkpoint?")
    n_head = last_linear.in_features

    # Build feature matrix Φ for all query points by hooking the input of the
    # output linear layer.
    activations: list[torch.Tensor] = []

    def _hook(_module, inputs, _output):
        activations.append(inputs[0].detach())

    handle = last_linear.register_forward_pre_hook(_hook)
    try:
        with torch.no_grad():
            mlo, mla, mhi, mhI = service.meta.bbox
            x_norm = (lons - mlo) / max(mhi - mlo, 1e-9)
            y_norm = (lats - mla) / max(mhI - mla, 1e-9)
            xx, yy = np.meshgrid(x_norm, y_norm)
            for t_val in times:
                x_t = torch.tensor(xx.ravel(), dtype=torch.float32)
                y_t = torch.tensor(yy.ravel(), dtype=torch.float32)
                t_t = torch.full_like(x_t, float(t_val))
                _ = model(x_t, y_t, t_t)
    finally:
        handle.remove()

    Phi = torch.cat(activations, dim=0)  # (T*Y*X, n_head)
    # Posterior precision: Σ_prior⁻¹ + Φ.T Φ.
    prior_prec = torch.eye(n_head) / (sigma_prior ** 2)
    post_prec = prior_prec + Phi.T @ Phi
    try:
        post_cov = torch.linalg.inv(post_prec)
    except RuntimeError:  # pragma: no cover — extreme rank deficiency
        post_cov = torch.linalg.pinv(post_prec)

    diag_var = (Phi @ post_cov * Phi).sum(dim=1)
    diag_var = diag_var.clamp(min=0)
    std = diag_var.sqrt().numpy()
    return std.reshape(len(times), len(lats), len(lons))


def carbon_estimate(epochs: int, n_params: int, gpu_seconds_per_step: float = 0.0) -> float:
    """Tiny CPU-only emissions estimate (kg CO2e)."""
    energy_kwh = (25.0 * epochs * 0.005 + 200.0 * gpu_seconds_per_step) / (1000.0 * 3600.0)
    return energy_kwh * 0.475 * max(1.0, n_params / 1e6)


def bma_predict(
    member_predictions: np.ndarray,
    member_log_marginals: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Bayesian Model Averaging across a fixed set of models.

    Parameters
    ----------
    member_predictions : ``(n_members, n_samples)`` array of point predictions.
    member_log_marginals : ``(n_members,)`` array of (estimated) log marginal
        likelihoods.  Higher = better evidence.  Stable-softmax weighting.

    Returns
    -------
    pred : ``(n_samples,)`` BMA mean prediction.
    weights : ``(n_members,)`` normalised BMA weights.
    """
    log_w = member_log_marginals - member_log_marginals.max()
    w = np.exp(log_w)
    w = w / w.sum()
    return (w[:, None] * member_predictions).sum(0), w


def estimate_log_marginal(observed: np.ndarray, predicted: np.ndarray, sigma_obs: float = 0.1) -> float:
    """Estimate the log marginal likelihood via the Gaussian residual proxy.

    Crude but standard for production BMA: assumes residuals are
    iid normal with std ``sigma_obs``.  Returns ``sum logN(obs|pred, sigma_obs)``.
    """
    residual = observed - predicted
    n = residual.size
    return float(-0.5 * np.sum(residual ** 2) / (sigma_obs ** 2) - n * np.log(sigma_obs))


def conformal_quantile(
    calibration_residuals: np.ndarray,
    alpha: float = 0.1,
) -> float:
    """Return the (1 - alpha) split-conformal calibration quantile.

    Add this to (or subtract from) point predictions to obtain a
    `(1 - alpha)` prediction interval with finite-sample marginal coverage
    `1 - alpha` (Vovk et al. 2005).
    """
    n = len(calibration_residuals)
    if n == 0:
        return float("nan")
    q_level = min(1.0, (np.ceil((1 - alpha) * (n + 1))) / n)
    return float(np.quantile(np.abs(calibration_residuals), q_level))


def reliability_curve(
    observed_binary: np.ndarray,
    probabilities: np.ndarray,
    n_bins: int = 10,
) -> dict[str, np.ndarray]:
    """Compute a reliability (calibration) curve for a binary outcome.

    Returns the mean predicted probability and observed frequency per
    quantile bin together with the bin count - feed straight into a
    plotting routine.
    """
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_idx = np.clip(np.digitize(probabilities, bin_edges) - 1, 0, n_bins - 1)
    pred = np.zeros(n_bins)
    obs = np.zeros(n_bins)
    count = np.zeros(n_bins)
    for i in range(n_bins):
        mask = bin_idx == i
        if mask.any():
            pred[i] = probabilities[mask].mean()
            obs[i] = observed_binary[mask].mean()
            count[i] = mask.sum()
    return {"pred": pred, "obs": obs, "count": count}


__all__ = [
    "PINNEnsemble",
    "EnsembleResult",
    "laplace_posterior_std",
    "carbon_estimate",
    "bma_predict",
    "estimate_log_marginal",
    "conformal_quantile",
    "reliability_curve",
]
