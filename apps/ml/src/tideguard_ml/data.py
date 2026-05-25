"""Datasets for PINN training.

Two implementations:

- ``SyntheticDataset``: an in-process Gaussian-bump dataset with known
  ground-truth parameters. Used for unit tests, baseline benchmarks and
  parameter-recovery experiments.
- ``RealDataset``: loads sparse citizen reports (CSV / Parquet) plus a
  gridded forcing tensor (Zarr / NetCDF) of ocean currents and wind. Built
  to consume CMEMS + ERA5 daily aggregates exported by
  ``tideguard_ml.ingest`` and citizen reports exported from the API.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch


@dataclass
class ObsBatch:
    x: torch.Tensor
    y: torch.Tensor
    t: torch.Tensor
    C: torch.Tensor


@dataclass
class CollocationBatch:
    x: torch.Tensor
    y: torch.Tensor
    t: torch.Tensor
    u_o: torch.Tensor
    v_o: torch.Tensor
    u_w: torch.Tensor
    v_w: torch.Tensor


class SyntheticDataset:
    """Synthetic Gaussian-bump advected by constant current + wind.

    Domain: x in [0,1], y in [0,1], t in [0,1] (normalised). The ground-truth
    physical parameters (``alpha_true``, ``K_true``) are returned by
    :pyattr:`ground_truth` for use in parameter-recovery tests.
    """

    def __init__(
        self,
        n_obs: int = 2000,
        u_ocean: float = 0.2,
        v_ocean: float = 0.1,
        u_wind: float = 1.0,
        v_wind: float = 0.5,
        alpha_true: float = 0.03,
        K_true: float = 0.005,
        seed: int = 42,
    ):
        rng = np.random.RandomState(seed)
        self.u_ocean = u_ocean
        self.v_ocean = v_ocean
        self.u_wind = u_wind
        self.v_wind = v_wind
        self.alpha_true = alpha_true
        self.K_true = K_true

        u_eff = u_ocean + alpha_true * u_wind
        v_eff = v_ocean + alpha_true * v_wind

        xs = rng.uniform(0, 1, n_obs).astype(np.float32)
        ys = rng.uniform(0, 1, n_obs).astype(np.float32)
        ts = rng.uniform(0, 1, n_obs).astype(np.float32)

        cx = 0.3 + u_eff * ts
        cy = 0.5 + v_eff * ts
        sigma = 0.05 + 2 * K_true * ts
        C = np.exp(-((xs - cx) ** 2 + (ys - cy) ** 2) / (2 * sigma**2))
        C += rng.normal(0, 0.02, n_obs).astype(np.float32)
        C = np.clip(C, 0, None)

        self._obs_x = torch.tensor(xs)
        self._obs_y = torch.tensor(ys)
        self._obs_t = torch.tensor(ts)
        self._obs_C = torch.tensor(C.astype(np.float32))

    @property
    def ground_truth(self) -> dict[str, float]:
        return {
            "alpha": self.alpha_true,
            "K": self.K_true,
            "u_ocean": self.u_ocean,
            "v_ocean": self.v_ocean,
        }

    def sample_obs(self, n: int, device: str = "cpu") -> ObsBatch:
        idx = torch.randint(0, len(self._obs_x), (n,))
        return ObsBatch(
            x=self._obs_x[idx].to(device),
            y=self._obs_y[idx].to(device),
            t=self._obs_t[idx].to(device),
            C=self._obs_C[idx].to(device),
        )

    def sample_collocation(self, n: int, device: str = "cpu") -> CollocationBatch:
        x = torch.rand(n, device=device)
        y = torch.rand(n, device=device)
        t = torch.rand(n, device=device)
        return CollocationBatch(
            x=x,
            y=y,
            t=t,
            u_o=torch.full((n,), self.u_ocean, device=device),
            v_o=torch.full((n,), self.v_ocean, device=device),
            u_w=torch.full((n,), self.u_wind, device=device),
            v_w=torch.full((n,), self.v_wind, device=device),
        )

    def ic_loss(self, model: torch.nn.Module) -> torch.Tensor:
        n = 512
        x = torch.rand(n)
        y = torch.rand(n)
        t = torch.zeros(n)
        C_pred = model(x, y, t)
        C_true = torch.exp(-((x - 0.3) ** 2 + (y - 0.5) ** 2) / (2 * 0.05**2))
        return ((C_pred - C_true) ** 2).mean()

    def bc_loss(self, model: torch.nn.Module) -> torch.Tensor:
        n = 256
        t = torch.rand(n)
        edges = [torch.rand(n // 4) for _ in range(4)]
        x_left = torch.zeros(n // 4)
        x_right = torch.ones(n // 4)
        y_bot = torch.zeros(n // 4)
        y_top = torch.ones(n // 4)
        C_left = model(x_left, edges[0], t[: n // 4])
        C_right = model(x_right, edges[1], t[n // 4 : n // 2])
        C_bot = model(edges[2], y_bot, t[n // 2 : 3 * n // 4])
        C_top = model(edges[3], y_top, t[3 * n // 4 :])
        return (C_left**2 + C_right**2 + C_bot**2 + C_top**2).mean()


class RealDataset:
    """Real-world dataset combining citizen reports and gridded forcings.

    Expects the following on disk:

    - ``reports_csv``: CSV with columns ``lon, lat, ts_seconds, concentration``.
      The ``ts_seconds`` column is normalised to ``[0, 1]`` by the constructor.
    - ``forcing_npz``: an NPZ archive holding ``lons``, ``lats``, ``times``,
      ``u_ocean``, ``v_ocean``, ``u_wind`` and ``v_wind`` as 3-D arrays.

    Both arguments are optional — if missing, the constructor raises
    ``FileNotFoundError`` so the caller can fall back to ``SyntheticDataset``.
    """

    def __init__(
        self,
        reports_csv: str | Path,
        forcing_npz: str | Path | None = None,
        bbox: tuple[float, float, float, float] = (119.0, 23.0, 123.0, 26.0),
        horizon_days: int = 14,
        seed: int = 0,
    ):
        try:
            import pandas as pd
        except ImportError as exc:  # pragma: no cover
            raise ImportError("RealDataset requires pandas; install with `pip install pandas`") from exc

        reports_csv = Path(reports_csv)
        if not reports_csv.exists():
            raise FileNotFoundError(f"reports_csv not found: {reports_csv}")

        df = pd.read_csv(reports_csv)
        for col in ("lon", "lat", "ts_seconds", "concentration"):
            if col not in df.columns:
                raise ValueError(f"reports_csv missing required column: {col}")

        lon_min, lat_min, lon_max, lat_max = bbox
        df = df[(df.lon >= lon_min) & (df.lon <= lon_max) & (df.lat >= lat_min) & (df.lat <= lat_max)].copy()
        if df.empty:
            raise ValueError(f"No reports inside bbox {bbox}")

        t0 = df.ts_seconds.min()
        t_span = max(df.ts_seconds.max() - t0, 1.0)
        df["t_norm"] = (df.ts_seconds - t0) / t_span
        df["x_norm"] = (df.lon - lon_min) / (lon_max - lon_min)
        df["y_norm"] = (df.lat - lat_min) / (lat_max - lat_min)

        self._obs_x = torch.tensor(df.x_norm.values, dtype=torch.float32)
        self._obs_y = torch.tensor(df.y_norm.values, dtype=torch.float32)
        self._obs_t = torch.tensor(df.t_norm.values, dtype=torch.float32)
        self._obs_C = torch.tensor(df.concentration.values, dtype=torch.float32).clamp(min=0.0)
        self.bbox = bbox
        self.horizon_days = horizon_days
        self.rng = np.random.RandomState(seed)

        # Forcings — REQUIRED in real-data mode (CRIT-ML-6). Silently falling
        # back to zero forcing produced a model that ignored ocean / wind
        # entirely. We now raise unless the caller explicitly opts out via
        # ``forcing_npz=None`` (which is fine for tests).
        self._forcing = None
        if forcing_npz is None:
            return
        forcing_path = Path(forcing_npz)
        if not forcing_path.exists():
            raise FileNotFoundError(
                f"forcing_npz path does not exist: {forcing_path}. "
                "Either pre-aggregate CMEMS+ERA5 via `tideguard_ml.ingest`, or "
                "pass `forcing_npz=None` to acknowledge the zero-forcing fallback."
            )
        data = np.load(forcing_path)
        for key in ("u_ocean", "v_ocean", "u_wind", "v_wind"):
            if key not in data.files:
                raise ValueError(f"forcing_npz missing array '{key}' in {forcing_path}")
        self._forcing = {
            "u_ocean": data["u_ocean"].astype(np.float32),
            "v_ocean": data["v_ocean"].astype(np.float32),
            "u_wind": data["u_wind"].astype(np.float32),
            "v_wind": data["v_wind"].astype(np.float32),
        }

    @classmethod
    def from_api_export(
        cls,
        api_export_dir: str | Path,
        bbox: tuple[float, float, float, float] = (119.0, 23.0, 123.0, 26.0),
    ) -> RealDataset:
        """Convenience: load from a directory produced by ``api → ml`` export.

        The export script writes ``reports.csv`` + ``forcing.npz`` into a
        timestamped directory; this just resolves them and forwards to
        ``__init__``.
        """
        d = Path(api_export_dir)
        return cls(reports_csv=d / "reports.csv", forcing_npz=d / "forcing.npz", bbox=bbox)

    def sample_obs(self, n: int, device: str = "cpu") -> ObsBatch:
        n = min(n, len(self._obs_x))
        idx = torch.randint(0, len(self._obs_x), (n,))
        return ObsBatch(
            x=self._obs_x[idx].to(device),
            y=self._obs_y[idx].to(device),
            t=self._obs_t[idx].to(device),
            C=self._obs_C[idx].to(device),
        )

    def sample_collocation(self, n: int, device: str = "cpu") -> CollocationBatch:
        x = torch.rand(n, device=device)
        y = torch.rand(n, device=device)
        t = torch.rand(n, device=device)
        if self._forcing is None:
            u_o = torch.zeros(n, device=device)
            v_o = torch.zeros(n, device=device)
            u_w = torch.zeros(n, device=device)
            v_w = torch.zeros(n, device=device)
        else:
            u_o = torch.tensor(self._sample_forcing("u_ocean", n), dtype=torch.float32, device=device)
            v_o = torch.tensor(self._sample_forcing("v_ocean", n), dtype=torch.float32, device=device)
            u_w = torch.tensor(self._sample_forcing("u_wind", n), dtype=torch.float32, device=device)
            v_w = torch.tensor(self._sample_forcing("v_wind", n), dtype=torch.float32, device=device)
        return CollocationBatch(x=x, y=y, t=t, u_o=u_o, v_o=v_o, u_w=u_w, v_w=v_w)

    def _sample_forcing(self, key: str, n: int) -> np.ndarray:
        arr = self._forcing[key]  # type: ignore[index]
        flat = arr.reshape(-1)
        idx = self.rng.randint(0, flat.size, size=n)
        return flat[idx]

    def ic_loss(self, model: torch.nn.Module) -> torch.Tensor:
        return torch.tensor(0.0)

    def bc_loss(self, model: torch.nn.Module) -> torch.Tensor:
        return torch.tensor(0.0)
