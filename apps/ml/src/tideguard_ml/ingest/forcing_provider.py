"""Forcing provider for inference and training (TASK-009).

Abstracts away "give me u_ocean / v_ocean / u_wind / v_wind at (lon, lat, t)"
so the API can run with either:

  * a cached NPZ produced by ``tideguard_ml.ingest`` (CMEMS + ERA5
    aggregated to the model grid), or
  * an on-the-fly synthetic field (Rim Current + climatological westerlies)
    that lets the system run when no upstream service is reachable.

The class is intentionally tiny: ``sample(...)`` returns four NumPy arrays
of the same shape as the input ``lon/lat/t`` arrays. The synthetic field is
the exact same one used by ``apps/ml/scripts/build_black_sea_validation.py``
so unit tests can compare values across the stack.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

DEFAULT_BBOX = (27.0, 40.0, 42.0, 47.0)


@dataclass
class ForcingSample:
    u_ocean: np.ndarray
    v_ocean: np.ndarray
    u_wind: np.ndarray
    v_wind: np.ndarray


class ForcingProvider:
    """Returns forcing fields at arbitrary (lon, lat, t_norm) points."""

    def __init__(
        self,
        cached_npz: str | Path | None = None,
        bbox: tuple[float, float, float, float] = DEFAULT_BBOX,
    ):
        self.bbox = bbox
        self._grid: dict[str, np.ndarray] | None = None
        if cached_npz is not None:
            p = Path(cached_npz)
            if p.exists():
                data = np.load(p)
                self._grid = {
                    "u_ocean": data["u_ocean"].astype(np.float32),
                    "v_ocean": data["v_ocean"].astype(np.float32),
                    "u_wind": data["u_wind"].astype(np.float32),
                    "v_wind": data["v_wind"].astype(np.float32),
                }

    @property
    def is_synthetic(self) -> bool:
        return self._grid is None

    def sample(self, lon: np.ndarray, lat: np.ndarray, t_norm: np.ndarray) -> ForcingSample:
        if self._grid is None:
            return self._synthetic(lon, lat, t_norm)
        return self._grid_sample(lon, lat, t_norm)

    def _synthetic(self, lon: np.ndarray, lat: np.ndarray, t_norm: np.ndarray) -> ForcingSample:
        cx = 0.5 * (self.bbox[0] + self.bbox[2])
        cy = 0.5 * (self.bbox[1] + self.bbox[3])
        dx = lon - cx
        dy = lat - cy
        norm = np.sqrt(dx ** 2 + dy ** 2) + 1e-6
        u_ocean = -dy / norm * 0.15
        v_ocean = dx / norm * 0.15
        t_phase = np.cos(2 * np.pi * t_norm)
        u_wind = 3.0 * (1.0 + 0.2 * t_phase)
        v_wind = -1.0 * (1.0 + 0.2 * t_phase)
        return ForcingSample(
            u_ocean=u_ocean.astype(np.float32),
            v_ocean=v_ocean.astype(np.float32),
            u_wind=np.broadcast_to(u_wind, u_ocean.shape).astype(np.float32),
            v_wind=np.broadcast_to(v_wind, u_ocean.shape).astype(np.float32),
        )

    def _grid_sample(self, lon: np.ndarray, lat: np.ndarray, t_norm: np.ndarray) -> ForcingSample:
        assert self._grid is not None
        nt, ny, nx = self._grid["u_ocean"].shape
        dlon = max(self.bbox[2] - self.bbox[0], 1e-9)
        dlat = max(self.bbox[3] - self.bbox[1], 1e-9)
        lon_idx = np.clip(
            ((lon - self.bbox[0]) / dlon * (nx - 1)).round().astype(int),
            0, nx - 1,
        )
        lat_idx = np.clip(
            ((lat - self.bbox[1]) / dlat * (ny - 1)).round().astype(int),
            0, ny - 1,
        )
        t_idx = np.clip(
            np.round(np.clip(t_norm, 0, 1) * (nt - 1)).astype(int),
            0, nt - 1,
        )
        return ForcingSample(
            u_ocean=self._grid["u_ocean"][t_idx, lat_idx, lon_idx],
            v_ocean=self._grid["v_ocean"][t_idx, lat_idx, lon_idx],
            u_wind=self._grid["u_wind"][t_idx, lat_idx, lon_idx],
            v_wind=self._grid["v_wind"][t_idx, lat_idx, lon_idx],
        )


__all__ = ["ForcingProvider", "ForcingSample", "DEFAULT_BBOX"]
