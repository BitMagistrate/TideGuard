"""Fourier Neural Operator baseline for the marine debris field.

Implements ``FNO2d`` following Li et al. 2021 (Neural Operator: Learning
Maps Between Function Spaces) — the canonical PDE-surrogate baseline.

Unlike the PINN, the FNO is a **data-driven** spectral operator: it learns
the mapping from forcing fields (ocean currents + wind) to concentration
snapshots directly, without explicit PDE residual constraints.  The two
models therefore complement each other in a Bayesian ensemble:

* PINN — physics-grounded but small (50 K params); generalises out of
  domain; weaker on small-scale spatial detail.
* FNO  — global spectral receptive field; strong on observed
  distributions; over-fits when forcing is out of the training cone.

Combining them via Bayesian Model Averaging (`uq.bma_predict`) is the
standard recipe for tier-1 climate ML papers.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class SpectralConv2d(nn.Module):
    """2D Fourier convolution layer (Li et al. 2021).

    Multiplies the lowest ``modes1 x modes2`` Fourier modes of the input
    by a learned complex weight tensor, then transforms back via ``irfft``.
    Captures global spatial structure with O(N log N) compute regardless
    of the grid resolution.
    """

    def __init__(self, in_channels: int, out_channels: int, modes1: int, modes2: int) -> None:
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.modes1 = modes1
        self.modes2 = modes2
        scale = 1.0 / (in_channels * out_channels)
        # Two complex weight tensors covering the positive and negative
        # frequency halves (rfft2 keeps the last axis halved).
        self.w1 = nn.Parameter(
            scale * torch.randn(in_channels, out_channels, modes1, modes2, dtype=torch.cfloat)
        )
        self.w2 = nn.Parameter(
            scale * torch.randn(in_channels, out_channels, modes1, modes2, dtype=torch.cfloat)
        )

    @staticmethod
    def _einsum(x: torch.Tensor, w: torch.Tensor) -> torch.Tensor:
        return torch.einsum("bixy,ioxy->boxy", x, w)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, _, H, W = x.shape
        x_ft = torch.fft.rfft2(x, norm="ortho")
        out_ft = torch.zeros(B, self.out_channels, H, x_ft.shape[-1], dtype=torch.cfloat, device=x.device)
        out_ft[:, :, : self.modes1, : self.modes2] = self._einsum(
            x_ft[:, :, : self.modes1, : self.modes2], self.w1
        )
        out_ft[:, :, -self.modes1 :, : self.modes2] = self._einsum(
            x_ft[:, :, -self.modes1 :, : self.modes2], self.w2
        )
        return torch.fft.irfft2(out_ft, s=(H, W), norm="ortho")


class FNO2d(nn.Module):
    """Stack of four spectral convolution + pointwise blocks.

    Input shape:  ``(B, in_channels, H, W)``
    Output shape: ``(B, H, W)`` — predicted concentration field.
    """

    def __init__(self, in_channels: int = 4, modes1: int = 8, modes2: int = 8, width: int = 24) -> None:
        super().__init__()
        self.modes1 = modes1
        self.modes2 = modes2
        self.width = width
        self.in_channels = in_channels
        self.fc0 = nn.Linear(in_channels, width)
        self.convs = nn.ModuleList(
            [SpectralConv2d(width, width, modes1, modes2) for _ in range(4)]
        )
        self.ws = nn.ModuleList([nn.Conv2d(width, width, 1) for _ in range(4)])
        self.fc1 = nn.Linear(width, 64)
        self.fc2 = nn.Linear(64, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Channels-last for the lifting MLP.
        x = self.fc0(x.permute(0, 2, 3, 1)).permute(0, 3, 1, 2)
        for s, w in zip(self.convs, self.ws):
            x = F.gelu(s(x) + w(x))
        x = x.permute(0, 2, 3, 1)
        x = F.gelu(self.fc1(x))
        return self.fc2(x).squeeze(-1)


def build_fno_training_batches(
    csv_path: Path | str,
    forcing_path: Path | str,
    bbox: tuple[float, float, float, float],
    grid_size: int = 32,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Build ``(inputs, targets)`` tensors for FNO training.

    The forcing tensor (``u_ocean``, ``v_ocean``, ``u_wind``, ``v_wind``)
    is reused as ``in_channels`` and the citizen reports are rasterised
    onto a ``grid_size`` x ``grid_size`` grid for the target.

    A single sample per forcing time step is generated; for ``nt = 24``
    forcing samples this gives 24 (input, target) pairs.
    """
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover
        raise ImportError("FNO training requires pandas") from exc

    csv_path = Path(csv_path)
    forcing_path = Path(forcing_path)
    df = pd.read_csv(csv_path)
    forcing = np.load(forcing_path)
    u_o, v_o = forcing["u_ocean"], forcing["v_ocean"]
    u_w, v_w = forcing["u_wind"], forcing["v_wind"]
    nt = u_o.shape[0]

    lon_min, lat_min, lon_max, lat_max = bbox
    # Resample forcing to grid_size×grid_size via bilinear interpolation.
    def _resample(a: np.ndarray) -> np.ndarray:
        ten = torch.from_numpy(a).float().unsqueeze(1)  # (T, 1, H, W)
        ten = F.interpolate(ten, size=(grid_size, grid_size), mode="bilinear", align_corners=False)
        return ten.squeeze(1).numpy()

    u_o, v_o = _resample(u_o), _resample(v_o)
    u_w, v_w = _resample(u_w), _resample(v_w)

    # Build the target concentration grid for each timestep by histogram-
    # binning the reports in time bins.
    t_min = float(df.ts_seconds.min())
    t_span = max(float(df.ts_seconds.max()) - t_min, 1.0)
    targets = np.zeros((nt, grid_size, grid_size), dtype=np.float32)
    counts = np.zeros((nt, grid_size, grid_size), dtype=np.float32)
    for _, row in df.iterrows():
        t_norm = (row.ts_seconds - t_min) / t_span
        ti = min(int(t_norm * nt), nt - 1)
        x = int((row.lon - lon_min) / max(lon_max - lon_min, 1e-9) * grid_size)
        y = int((row.lat - lat_min) / max(lat_max - lat_min, 1e-9) * grid_size)
        x = max(0, min(grid_size - 1, x))
        y = max(0, min(grid_size - 1, y))
        targets[ti, y, x] += row.concentration
        counts[ti, y, x] += 1.0
    # Use mean concentration in each occupied cell, zero elsewhere.
    targets = np.where(counts > 0, targets / np.clip(counts, 1.0, None), 0.0)

    inputs = np.stack([u_o, v_o, u_w, v_w], axis=1)  # (T, 4, H, W)
    return torch.from_numpy(inputs).float(), torch.from_numpy(targets).float()


def load_fno_checkpoint(path: Path | str, device: str = "cpu") -> FNO2d:
    ckpt = torch.load(str(path), map_location=device, weights_only=False)
    cfg = ckpt.get("config", {"in_channels": 4, "modes1": 8, "modes2": 8, "width": 24})
    model = FNO2d(
        in_channels=int(cfg.get("in_channels", 4)),
        modes1=int(cfg.get("modes1", 8)),
        modes2=int(cfg.get("modes2", 8)),
        width=int(cfg.get("width", 24)),
    )
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    model.to(device)
    return model


__all__ = [
    "FNO2d",
    "SpectralConv2d",
    "build_fno_training_batches",
    "load_fno_checkpoint",
]
