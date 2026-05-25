"""Conditional PINN for marine debris transport (2D advection-diffusion).

Per TIDEGUARD_AUDIT.md TASK-001 (CRIT-ML-1) the network now takes the local
forcing — ocean currents, wind — as additional inputs:

    forward(x, y, t, u_ocean=0, v_ocean=0, u_wind=0, v_wind=0)

This makes the model **conditional**: a single trained network can be queried
for "what would the debris look like if the current shifted +0.3 m/s east?"
The previous implementation hard-coded the forcing into the data loader's
collocation batch, so the network learned only the marginal solution and
could not be re-used on a different forcing field.

The PDE residual still uses the same advection-diffusion form
``dC/dt + ∇·((u_o + α u_w) C) − K ∇²C + λ C = 0``
but now `u_ocean/u_wind` live in the network input rather than in a
dataset-private buffer.

**SIREN upgrade (P0-1):** the activation function is now configurable
between ``tanh`` (legacy) and ``siren`` (Sitzmann et al. 2020).  SIREN
preserves high-frequency information through sinusoidal activations
and dramatically improves the fit of small-scale spatial detail
(coastal hotspots) on the same parameter budget.

**Multi-physics extension (T14):** the residual now optionally includes a
Stokes drift term (``alpha_stokes * u_wind``) on top of windage, and a
biofouling sink that grows linearly with time, ``lam_eff(t) = lam + lam_bio * t``.
Stokes drift accounts for wave-driven surface transport of buoyant
plastics (Onink et al. 2019); biofouling captures the loss of buoyancy
that sinks plastic out of the surface layer (Egger et al. 2020).

Backwards-compat: ``forward(x, y, t)`` keeps working — forcing channels
default to zero, which matches the synthetic-dataset training regime used in
``apps/ml/tests/test_pinn.py``.
"""

from __future__ import annotations

import math
from typing import Literal

import torch
import torch.nn as nn

NUM_SPACETIME_CHANNELS = 3   # x, y, t
NUM_FORCING_CHANNELS = 4     # u_o, v_o, u_w, v_w


def fourier_features(coords: torch.Tensor, num_freq: int = 8) -> torch.Tensor:
    """Random Fourier features for a vector of input channels."""
    freqs = 2.0 ** torch.arange(num_freq, device=coords.device).float()
    angles = coords.unsqueeze(-1) * freqs * math.pi
    return torch.cat([angles.sin(), angles.cos()], dim=-1).flatten(start_dim=-2)


class Sine(nn.Module):
    """Sinusoidal activation used in SIREN (Sitzmann et al. 2020)."""

    def __init__(self, w0: float = 1.0) -> None:
        super().__init__()
        self.w0 = w0

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.sin(self.w0 * x)


def _siren_init(linear: nn.Linear, w0: float, is_first: bool = False) -> None:
    fan_in = linear.in_features
    bound = (1.0 / fan_in) if is_first else (math.sqrt(6.0 / fan_in) / w0)
    with torch.no_grad():
        linear.weight.uniform_(-bound, bound)
        if linear.bias is not None:
            linear.bias.zero_()


class PINN(nn.Module):
    """Conditional Physics-Informed Neural Network.

    Architecture
    ------------
    Fourier features over 7 channels (x, y, t, u_o, v_o, u_w, v_w) →
    ``depth`` x Linear(hidden, hidden, act) → Linear(hidden, 1).

    Learnable physical parameters:
        ``log(alpha)``         windage coefficient
        ``log(K)``             eddy diffusion (m²/s)
        ``log(lambda)``        beaching / sinking rate (1/s)
        ``log(alpha_stokes)``  Stokes drift coefficient (≈ 0.013)
        ``log(lambda_bio)``    biofouling-driven sink growth rate

    ``activation``: either ``"tanh"`` (legacy) or ``"siren"``.
    ``w0``: SIREN first-layer frequency (default 30 per the paper).
    """

    def __init__(
        self,
        hidden: int = 128,
        depth: int = 6,
        num_freq: int = 8,
        activation: Literal["tanh", "siren"] = "tanh",
        w0: float = 30.0,
    ):
        super().__init__()
        in_dim = (NUM_SPACETIME_CHANNELS + NUM_FORCING_CHANNELS) * 2 * num_freq
        layers: list[nn.Module]
        if activation == "siren":
            first = nn.Linear(in_dim, hidden)
            _siren_init(first, w0=w0, is_first=True)
            layers = [first, Sine(w0)]
            for _ in range(depth - 1):
                lin = nn.Linear(hidden, hidden)
                _siren_init(lin, w0=1.0)
                layers += [lin, Sine(1.0)]
            out = nn.Linear(hidden, 1)
            _siren_init(out, w0=1.0)
            layers.append(out)
        else:
            layers = [nn.Linear(in_dim, hidden), nn.Tanh()]
            for _ in range(depth - 1):
                layers += [nn.Linear(hidden, hidden), nn.Tanh()]
            layers += [nn.Linear(hidden, 1)]
        self.net = nn.Sequential(*layers)
        self.log_alpha = nn.Parameter(torch.tensor(math.log(0.03)))
        self.log_K = nn.Parameter(torch.tensor(math.log(100.0)))
        self.log_lam = nn.Parameter(torch.tensor(math.log(1e-6)))
        self.log_alpha_stokes = nn.Parameter(torch.tensor(math.log(0.013)))
        self.log_lam_bio = nn.Parameter(torch.tensor(math.log(1e-7)))
        self.num_freq = num_freq
        self.activation = activation
        self.w0 = w0
        self.hidden = hidden
        self.depth = depth

    @property
    def alpha(self) -> torch.Tensor:
        """Windage coefficient (typically 0.02-0.04)."""
        return torch.exp(self.log_alpha)

    @property
    def K(self) -> torch.Tensor:
        """Diffusion coefficient (m^2/s)."""
        return torch.exp(self.log_K)

    @property
    def lam(self) -> torch.Tensor:
        """Beaching / sinking rate (1/s)."""
        return torch.exp(self.log_lam)

    @property
    def alpha_stokes(self) -> torch.Tensor:
        """Stokes drift coefficient (Onink et al. 2019, typ. 0.01)."""
        return torch.exp(self.log_alpha_stokes)

    @property
    def lam_bio(self) -> torch.Tensor:
        """Biofouling-driven sinking growth (1/s²)."""
        return torch.exp(self.log_lam_bio)

    def forward(
        self,
        x: torch.Tensor,
        y: torch.Tensor,
        t: torch.Tensor,
        u_ocean: torch.Tensor | None = None,
        v_ocean: torch.Tensor | None = None,
        u_wind: torch.Tensor | None = None,
        v_wind: torch.Tensor | None = None,
    ) -> torch.Tensor:
        zero = torch.zeros_like(x)
        u_o = u_ocean if u_ocean is not None else zero
        v_o = v_ocean if v_ocean is not None else zero
        u_w = u_wind if u_wind is not None else zero
        v_w = v_wind if v_wind is not None else zero
        coords = torch.stack([x, y, t, u_o, v_o, u_w, v_w], dim=-1)
        h = fourier_features(coords, self.num_freq)
        return self.net(h).squeeze(-1)


def pde_residual(
    model: PINN,
    x: torch.Tensor,
    y: torch.Tensor,
    t: torch.Tensor,
    u_ocean: torch.Tensor,
    v_ocean: torch.Tensor,
    u_wind: torch.Tensor,
    v_wind: torch.Tensor,
    multi_physics: bool = False,
) -> torch.Tensor:
    """PDE residual of the conditional model at sampled collocation points.

    The gradient is taken **only** wrt (x, y, t) — the forcing channels are
    held fixed (they are the "u" in the advection-diffusion equation, not
    the model's spatial coordinates).

    When ``multi_physics`` is True the effective velocity carries the Stokes
    drift term and the beaching rate grows linearly with time
    (biofouling-driven sinking).
    """
    x = x.requires_grad_(True)
    y = y.requires_grad_(True)
    t = t.requires_grad_(True)
    C = model(x, y, t, u_ocean, v_ocean, u_wind, v_wind)

    grad = torch.autograd.grad(C.sum(), [x, y, t], create_graph=True)
    Cx, Cy, Ct = grad[0], grad[1], grad[2]
    Cxx = torch.autograd.grad(Cx.sum(), x, create_graph=True)[0]
    Cyy = torch.autograd.grad(Cy.sum(), y, create_graph=True)[0]

    if multi_physics:
        u = u_ocean + model.alpha * u_wind + model.alpha_stokes * u_wind
        v = v_ocean + model.alpha * v_wind + model.alpha_stokes * v_wind
        lam_eff = model.lam + model.lam_bio * t
    else:
        u = u_ocean + model.alpha * u_wind
        v = v_ocean + model.alpha * v_wind
        lam_eff = model.lam
    adv = u * Cx + v * Cy
    diff = model.K * (Cxx + Cyy)
    res = Ct + adv - diff + lam_eff * C
    return res


def infer_arch_from_state_dict(state: dict) -> dict:
    """Auto-infer ``hidden``, ``depth``, ``num_freq`` from a saved state dict.

    Used by the inference service so checkpoints of different sizes load
    uniformly.  Activation cannot be inferred from weights alone; callers
    should read it from the saved meta block.
    """
    hidden = int(state["net.0.bias"].shape[0])
    in_dim = int(state["net.0.weight"].shape[1])
    if in_dim % 14 == 0:
        num_freq = max(1, in_dim // 14)
    elif in_dim % 6 == 0:
        num_freq = max(1, in_dim // 6)
    else:
        num_freq = max(1, in_dim // 14)
    linear_idxs = sorted(
        {int(k.split(".")[1]) for k in state if k.startswith("net.") and k.endswith(".weight")}
    )
    depth = max(1, len(linear_idxs) - 1)
    return {"hidden": hidden, "num_freq": num_freq, "depth": depth}


__all__ = [
    "PINN",
    "Sine",
    "pde_residual",
    "fourier_features",
    "infer_arch_from_state_dict",
]
