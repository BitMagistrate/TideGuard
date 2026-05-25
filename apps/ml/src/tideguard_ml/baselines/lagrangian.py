"""Lagrangian particle-tracking baseline.

A deterministic, physics-only implementation of the same advection-diffusion
process the PINN is approximating. Useful as a sanity check: if the PINN
loses to this baseline, something is broken.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class LagrangianBaseline:
    """Forward-Euler integration of (u_ocean + alpha*u_wind, v_ocean + alpha*v_wind).

    Uses ``n_particles`` discrete particles sampled from the initial
    concentration field, then advected by per-step velocities. Diffusion is
    modelled as Gaussian smoothing of the density estimate at each step.
    """

    alpha: float = 0.03
    K: float = 1e-3
    dt_seconds: float = 60 * 60 * 24  # one day
    n_particles: int = 5000
    seed: int = 0

    def predict_grid(
        self,
        initial_C: np.ndarray,
        u_ocean: np.ndarray,
        v_ocean: np.ndarray,
        u_wind: np.ndarray,
        v_wind: np.ndarray,
        horizon_days: int,
    ) -> np.ndarray:
        """Return ``(horizon_days, *initial_C.shape)`` forecast."""
        rng = np.random.RandomState(self.seed)
        ny, nx = initial_C.shape
        # Sample initial particle positions weighted by initial_C
        probs = initial_C.ravel().clip(min=0)
        if probs.sum() == 0:
            probs = np.ones_like(probs)
        probs = probs / probs.sum()
        idx = rng.choice(probs.size, size=self.n_particles, p=probs)
        py = idx // nx
        px = idx % nx
        positions = np.stack([px.astype(float), py.astype(float)], axis=1)

        diffusion_std = float(np.sqrt(2 * self.K * self.dt_seconds))
        out = np.zeros((horizon_days, ny, nx), dtype=np.float32)
        u_eff = u_ocean + self.alpha * u_wind
        v_eff = v_ocean + self.alpha * v_wind

        for d in range(horizon_days):
            # Apply velocity (assumed constant over the horizon for this stub)
            positions[:, 0] += np.atleast_1d(u_eff).mean()
            positions[:, 1] += np.atleast_1d(v_eff).mean()
            # Diffusion (random walk)
            positions += rng.normal(0, diffusion_std, size=positions.shape)
            positions = np.clip(positions, [0, 0], [nx - 1, ny - 1])
            # Rasterise back to grid
            histogram, _, _ = np.histogram2d(
                positions[:, 1],
                positions[:, 0],
                bins=[ny, nx],
                range=[[0, ny], [0, nx]],
            )
            total = histogram.sum()
            out[d] = (histogram / total).astype(np.float32) if total > 0 else histogram.astype(np.float32)
        return out
