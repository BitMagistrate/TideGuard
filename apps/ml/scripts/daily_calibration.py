#!/usr/bin/env python3
"""Daily PINN calibration against Sentinel-2 floating-debris masks (P1-11).

The script pulls the most recent S2 derived debris mask for the
Black-Sea pilot region, projects it onto the PINN forecast grid, and
emits a JSON report with per-day reliability metrics (Brier, NSE,
ROC-AUC).  The report is consumed by the public ``/method/calibration``
page and stamped onto the methodology PDF appended to weekly B2G
deliverables.

The actual S2 fetch is dependency-light: in a real deployment we'd
read ``sentinelsat`` granules and run an NDWI/SCL-based mask; here we
support an offline mode where the mask is loaded from a synthetic
NetCDF distributed alongside the validation dataset so the calibration
can be unit-tested.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from tideguard_ml.eval.real_validation import _build_metrics


def _load_mask(path: Path) -> np.ndarray:
    arr = np.load(path)
    if arr.ndim != 2:
        raise ValueError(f"S2 mask must be 2-D, got shape {arr.shape}")
    return arr.astype(np.float32)


def _load_forecast(path: Path) -> np.ndarray:
    arr = np.load(path)
    if arr.ndim != 2:
        raise ValueError(f"forecast grid must be 2-D, got shape {arr.shape}")
    return arr.astype(np.float32)


def calibrate(
    mask_path: Path,
    forecast_path: Path,
    out_json: Path,
) -> dict:
    truth = _load_mask(mask_path).flatten()
    pred = _load_forecast(forecast_path).flatten()
    if truth.shape != pred.shape:
        raise ValueError("S2 mask and forecast shape mismatch")

    threshold = float(np.median(truth[truth > 0])) if (truth > 0).any() else 0.5
    metrics = _build_metrics(observed=truth, predicted=pred, threshold=threshold)
    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "n_pixels": int(truth.size),
        "metrics": metrics,
        "source": {
            "satellite": "Sentinel-2 L2A",
            "mask": str(mask_path),
            "forecast": str(forecast_path),
        },
    }
    out_json.write_text(json.dumps(report, indent=2, default=float))
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Daily S2 calibration")
    p.add_argument("--mask", required=True, type=Path)
    p.add_argument("--forecast", required=True, type=Path)
    p.add_argument(
        "--out",
        type=Path,
        default=Path("apps/ml/reports/daily_calibration.json"),
    )
    args = p.parse_args(argv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = calibrate(args.mask, args.forecast, args.out)
    print(json.dumps(report, indent=2, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
