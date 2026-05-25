"""Evaluation utilities for TideGuard PINN against real observations.

This subpackage covers everything the Stockholm Junior Water Prize and
RELX juries explicitly ask for but the original benchmark harness did not
provide:

- ``metrics``: scalar skill scores (RMSE, MAE, NSE, Brier, ROC-AUC).
- ``statistical_tests``: Diebold-Mariano test + bootstrap 95% CI on the
  difference of forecast errors.
- ``calibration``: reliability diagram, expected calibration error (ECE)
  and post-hoc temperature scaling for binary exceedance forecasts.
- ``exceedance``: probability-of-exceedance maps from an ensemble of
  forecasters (the "show me where the hotspot will be, not the mean"
  feature jurors keep asking for).
- ``real_validation``: end-to-end CLI that joins a CSV of real
  observations with a PINN checkpoint (or ensemble of checkpoints) and
  writes a structured ``eval_report.json``.
"""

from tideguard_ml.eval.calibration import (
    ECEResult,
    expected_calibration_error,
    reliability_diagram,
    temperature_scale,
)
from tideguard_ml.eval.exceedance import probability_of_exceedance
from tideguard_ml.eval.metrics import (
    brier_score,
    mae,
    nse,
    rmse,
    roc_auc,
)
from tideguard_ml.eval.statistical_tests import (
    bootstrap_rmse_ci,
    diebold_mariano,
)

__all__ = [
    "ECEResult",
    "bootstrap_rmse_ci",
    "brier_score",
    "diebold_mariano",
    "expected_calibration_error",
    "mae",
    "nse",
    "probability_of_exceedance",
    "reliability_diagram",
    "rmse",
    "roc_auc",
    "temperature_scale",
]
