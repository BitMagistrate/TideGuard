"""Climatology baseline.

The "climatology" forecast is the long-term monthly mean of the
observed series at each location — a much stronger baseline than
persistence for any field with seasonal structure (marine debris
concentration peaks in the wet season near river mouths, then decays).

The WinPlan §1.4 requires a third baseline beyond persistence and
Lagrangian; this is it. We expose the same ``predict_grid`` API as the
other baselines so :mod:`tideguard_ml.baselines.benchmark` can call it
without a special case.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class ClimatologyBaseline:
    """Predict the long-term mean field, optionally per-month.

    Args:
        monthly_means: optional ``(12, n_lat, n_lon)`` array of monthly
            climatologies. If supplied, :meth:`predict_grid` will rotate
            through them starting at ``start_month``.
        global_mean_field: fallback ``(n_lat, n_lon)`` field used when
            ``monthly_means`` is None.
    """

    monthly_means: np.ndarray | None = None
    global_mean_field: np.ndarray | None = None
    start_month: int = 1  # 1 = January
    history: list[np.ndarray] = field(default_factory=list)

    @classmethod
    def fit(
        cls,
        observations: np.ndarray,
        months: np.ndarray | None = None,
    ) -> ClimatologyBaseline:
        """Build the climatology field from a stack of historical grids.

        Args:
            observations: shape ``(T, n_lat, n_lon)``.
            months: optional 1-indexed month for each entry along axis 0.
                If supplied, a monthly climatology is computed; otherwise
                a single global mean field is stored.
        """
        observations = np.asarray(observations, dtype=np.float64)
        if observations.ndim != 3:
            raise ValueError(f"observations must be 3-D (T, lat, lon); got {observations.shape}")
        if months is None:
            return cls(global_mean_field=observations.mean(axis=0))

        months = np.asarray(months, dtype=int)
        if months.shape[0] != observations.shape[0]:
            raise ValueError("months must align with observations along axis 0")
        monthly = np.zeros((12, observations.shape[1], observations.shape[2]), dtype=np.float64)
        for m in range(1, 13):
            mask = months == m
            if not np.any(mask):
                monthly[m - 1] = observations.mean(axis=0)
            else:
                monthly[m - 1] = observations[mask].mean(axis=0)
        return cls(monthly_means=monthly)

    def predict_grid(
        self,
        initial_C: np.ndarray | None,
        horizon_days: int,
    ) -> np.ndarray:
        """Return a ``(horizon_days, n_lat, n_lon)`` climatology forecast.

        ``initial_C`` is accepted for API symmetry with the other
        baselines but only used to infer the spatial shape when no
        climatology has been fitted yet.
        """
        if self.monthly_means is not None:
            n_lat, n_lon = self.monthly_means.shape[1:]
            out = np.zeros((horizon_days, n_lat, n_lon), dtype=np.float32)
            for d in range(horizon_days):
                # Each step is roughly 1 day; cycle through months every
                # 30 days. This is a coarse approximation but matches the
                # benchmark which spans <= 14 days.
                month_idx = (self.start_month - 1 + d // 30) % 12
                out[d] = self.monthly_means[month_idx].astype(np.float32)
            return out

        if self.global_mean_field is not None:
            field_ = self.global_mean_field.astype(np.float32)
            return np.broadcast_to(field_[None, ...], (horizon_days, *field_.shape)).copy()

        # No fit yet — fall back to the initial field if provided.
        if initial_C is None:
            raise ValueError("ClimatologyBaseline.fit was never called; pass initial_C as a last resort")
        init = np.asarray(initial_C, dtype=np.float32)
        return np.broadcast_to(init[None, ...], (horizon_days, *init.shape)).copy()
