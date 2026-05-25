"""Persistence baseline: tomorrow looks like today.

This is the simplest possible forecast and the absolute floor any honest
data-driven model must beat. We expose it through the same ``predict`` API
as the PINN so the benchmark harness can compare apples to apples.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class PersistenceBaseline:
    """Repeat the initial concentration field for every forecast horizon."""

    def predict_grid(
        self,
        initial_C: np.ndarray,
        horizon_days: int,
    ) -> np.ndarray:
        """Return an ``(horizon_days, *initial_C.shape)`` array of repeats."""
        return np.broadcast_to(initial_C[None, ...], (horizon_days, *initial_C.shape)).copy()
