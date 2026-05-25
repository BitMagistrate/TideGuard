"""Inference service for TideGuard PINN model.

Per TIDEGUARD_AUDIT.md TASK-002 (CRIT-ML-2) the service now holds a
``TrainingMeta`` block (bbox, t0, t_span, forcing source) loaded from the
checkpoint and uses it to normalise lon/lat/time. Calls with an out-of-domain
bbox are rejected with ``OutOfDomainError`` (the API converts that to HTTP
422). When no metadata is in the checkpoint the service falls back to a
``Domain('black-sea')`` default so legacy synthetic checkpoints still run.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch

from tideguard_ml.pinn import PINN

logger = logging.getLogger(__name__)


class OutOfDomainError(ValueError):
    """Raised when the requested bbox lies outside the trained domain."""


@dataclass
class TrainingMeta:
    """Geographic + temporal metadata embedded in a checkpoint."""

    domain: str = "black-sea"
    bbox: tuple[float, float, float, float] = (27.0, 40.0, 42.0, 47.0)
    horizon_days: int = 14
    forcing_source: str = "synthetic"
    git_sha: str = "v0.2.0"
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "bbox": list(self.bbox),
            "horizon_days": self.horizon_days,
            "forcing_source": self.forcing_source,
            "git_sha": self.git_sha,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> TrainingMeta:
        return cls(
            domain=payload.get("domain", "black-sea"),
            bbox=tuple(payload.get("bbox", (27.0, 40.0, 42.0, 47.0))),  # type: ignore[arg-type]
            horizon_days=int(payload.get("horizon_days", 14)),
            forcing_source=payload.get("forcing_source", "synthetic"),
            git_sha=payload.get("git_sha", "v0.2.0"),
            extra=dict(payload.get("extra", {})),
        )


@dataclass
class ForecastResult:
    """Grid of predicted debris concentration."""

    lons: np.ndarray
    lats: np.ndarray
    times: np.ndarray
    concentration: np.ndarray  # (n_times, n_lat, n_lon)
    meta: TrainingMeta | None = None


class PINNInferenceService:
    """Load a trained PINN checkpoint and run inference in lon/lat."""

    def __init__(self, checkpoint_path: str | Path, device: str = "cpu", *, allow_pad: float = 0.05):
        from tideguard_ml.pinn import infer_arch_from_state_dict

        self.device = device
        self.allow_pad = allow_pad
        ckpt = torch.load(str(checkpoint_path), map_location=device, weights_only=False)
        state = ckpt["model_state_dict"]
        meta_dict = ckpt.get("meta", {}) or {}
        extra = dict(meta_dict.get("extra", {}))
        arch = infer_arch_from_state_dict(state)
        activation = extra.get("activation", "tanh")
        w0 = float(extra.get("w0", 1.0))
        self.model = PINN(
            hidden=arch["hidden"],
            depth=arch["depth"],
            num_freq=arch["num_freq"],
            activation=activation,  # type: ignore[arg-type]
            w0=w0,
        )
        self.model.load_state_dict(state, strict=False)
        self.model.eval()
        self.model.to(device)
        self.meta = TrainingMeta.from_dict(meta_dict)

    def _check_domain(self, bbox: tuple[float, float, float, float]) -> None:
        lon_min, lat_min, lon_max, lat_max = bbox
        mlo, mla, mhi, mhI = self.meta.bbox
        span_lon = mhi - mlo
        span_lat = mhI - mla
        pad_lon = self.allow_pad * span_lon
        pad_lat = self.allow_pad * span_lat
        if (
            lon_min < mlo - pad_lon
            or lon_max > mhi + pad_lon
            or lat_min < mla - pad_lat
            or lat_max > mhI + pad_lat
        ):
            raise OutOfDomainError(
                f"requested bbox {bbox} outside trained domain {self.meta.domain} bbox {self.meta.bbox}"
            )

    @torch.no_grad()
    def predict(
        self,
        lon_min: float,
        lon_max: float,
        lat_min: float,
        lat_max: float,
        horizon_days: int = 7,
        resolution: int = 50,
    ) -> ForecastResult:
        """Generate a forecast grid in *real* lon/lat (TASK-002)."""
        self._check_domain((lon_min, lat_min, lon_max, lat_max))
        lons = np.linspace(lon_min, lon_max, resolution)
        lats = np.linspace(lat_min, lat_max, resolution)
        # Normalise into the [0,1]² training domain so the network sees
        # exactly the inputs it was trained on.
        mlo, mla, mhi, mhI = self.meta.bbox
        x_norm = (lons - mlo) / max(mhi - mlo, 1e-9)
        y_norm = (lats - mla) / max(mhI - mla, 1e-9)
        xx, yy = np.meshgrid(x_norm, y_norm)

        times = np.linspace(0.0, horizon_days / self.meta.horizon_days, horizon_days)
        concentration = np.zeros((horizon_days, resolution, resolution), dtype=np.float32)
        for ti, t_val in enumerate(times):
            x_t = torch.tensor(xx.ravel(), dtype=torch.float32, device=self.device)
            y_t = torch.tensor(yy.ravel(), dtype=torch.float32, device=self.device)
            t_t = torch.full_like(x_t, float(t_val))
            C = self.model(x_t, y_t, t_t).cpu().numpy()
            concentration[ti] = C.reshape(resolution, resolution)
        return ForecastResult(
            lons=lons,
            lats=lats,
            times=np.arange(horizon_days),
            concentration=np.clip(concentration, 0, None),
            meta=self.meta,
        )
