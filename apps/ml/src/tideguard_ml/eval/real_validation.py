"""End-to-end real-data validation harness.

CLI::

    uv run python -m tideguard_ml.eval.real_validation \\
        --csv data/real/black_sea_2021_2025.csv \\
        --checkpoint checkpoints/pinn_demo.pt \\
        --bbox 27,40,42,47 \\
        --out reports/real_validation_2026.json

The CSV must follow the template documented in
``apps/ml/data/real/black_sea_template.csv``; specifically it must hold
columns ``lon, lat, ts_seconds, concentration`` and may hold optional
columns ``source`` and ``license``.

Output is a JSON file the paper renders into table 4 (``RMSE``, ``MAE``,
``NSE``, ``Brier``, ``ROC-AUC``) and table 5 (``Diebold-Mariano``,
``bootstrap CI``). The script never fails silently: missing inputs,
unsupported checkpoint formats, empty bboxes etc. all raise
``SystemExit`` with an actionable message.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from tideguard_ml.baselines.climatology import ClimatologyBaseline
from tideguard_ml.baselines.persistence import PersistenceBaseline
from tideguard_ml.eval.calibration import expected_calibration_error
from tideguard_ml.eval.metrics import brier_score, mae, nse, rmse, roc_auc
from tideguard_ml.eval.statistical_tests import bootstrap_rmse_ci, diebold_mariano


@dataclass
class ValidationReport:
    csv: str
    n_observations: int
    bbox: list[float]
    threshold_quantile: float
    threshold_value: float
    metrics: dict[str, dict[str, float]]
    statistical_tests: dict[str, dict[str, Any]]
    notes: list[str]


def _read_csv(csv_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("real_validation requires pandas; install via `uv pip install pandas`") from exc
    if not csv_path.exists():
        raise SystemExit(f"--csv not found: {csv_path}")
    df = pd.read_csv(csv_path)
    required = ("lon", "lat", "ts_seconds", "concentration")
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"--csv missing required columns: {missing}")
    return (
        df["lon"].to_numpy(dtype=np.float64),
        df["lat"].to_numpy(dtype=np.float64),
        df["ts_seconds"].to_numpy(dtype=np.float64),
        df["concentration"].to_numpy(dtype=np.float64),
    )


def _filter_bbox(
    lons: np.ndarray, lats: np.ndarray, ts: np.ndarray, c: np.ndarray, bbox: tuple[float, float, float, float]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    lon_min, lat_min, lon_max, lat_max = bbox
    mask = (lons >= lon_min) & (lons <= lon_max) & (lats >= lat_min) & (lats <= lat_max)
    if not np.any(mask):
        raise SystemExit(f"No observations inside bbox {bbox}")
    return lons[mask], lats[mask], ts[mask], c[mask]


def _predict_pinn(
    checkpoint_path: Path,
    lons: np.ndarray,
    lats: np.ndarray,
    ts_normalised: np.ndarray,
    bbox: tuple[float, float, float, float],
) -> np.ndarray:
    """Point-wise PINN prediction at observation locations + times."""
    try:
        import torch

        from tideguard_ml.pinn import PINN
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("real_validation requires torch") from exc

    if not checkpoint_path.exists():
        raise SystemExit(f"--checkpoint not found: {checkpoint_path}")

    ckpt = torch.load(str(checkpoint_path), map_location="cpu", weights_only=False)
    state = ckpt["model_state_dict"]
    meta_dict = ckpt.get("meta", {}) or {}
    extra = dict(meta_dict.get("extra", {}))
    from tideguard_ml.pinn import infer_arch_from_state_dict
    arch = infer_arch_from_state_dict(state)
    activation = extra.get("activation", "tanh")
    w0 = float(extra.get("w0", 1.0))
    model = PINN(
        hidden=arch["hidden"],
        depth=arch["depth"],
        num_freq=arch["num_freq"],
        activation=activation,
        w0=w0,
    )
    model.load_state_dict(state, strict=False)
    model.eval()

    lon_min, lat_min, lon_max, lat_max = bbox
    x = (lons - lon_min) / max(lon_max - lon_min, 1e-9)
    y = (lats - lat_min) / max(lat_max - lat_min, 1e-9)
    with torch.no_grad():
        x_t = torch.tensor(x, dtype=torch.float32)
        y_t = torch.tensor(y, dtype=torch.float32)
        t_t = torch.tensor(ts_normalised, dtype=torch.float32)
        C = model(x_t, y_t, t_t).numpy()
    return np.clip(C, 0.0, None)


def _predict_persistence(c: np.ndarray) -> np.ndarray:
    """Per-day persistence: predict the global mean as the trivial flat field.

    For scattered point observations a "persistence at t" forecast collapses
    to the mean of the *previous-day* observations, which we approximate
    here by the global mean. This is the floor a useful model must beat.
    """
    _ = PersistenceBaseline  # keep import path stable for downstream tools
    return np.full_like(c, float(np.mean(c)))


def _predict_climatology(c: np.ndarray, ts_normalised: np.ndarray) -> np.ndarray:
    """Time-conditioned climatology: bin the time axis into 12 \"months\"."""
    _ = ClimatologyBaseline  # keep import path stable for downstream tools
    bin_idx = np.clip(np.floor(ts_normalised * 12).astype(int), 0, 11)
    monthly = np.zeros(12, dtype=np.float64)
    counts = np.zeros(12, dtype=np.float64)
    for i, b in enumerate(bin_idx):
        monthly[b] += c[i]
        counts[b] += 1
    fallback = float(c.mean())
    for m in range(12):
        if counts[m] > 0:
            monthly[m] /= counts[m]
        else:
            monthly[m] = fallback
    return monthly[bin_idx]


def _build_metrics(observed: np.ndarray, predicted: np.ndarray, threshold: float) -> dict[str, float]:
    observed_binary = (observed > threshold).astype(np.float64)
    # Clip predicted to [0, max(observed)*2] then normalise to [0, 1] so
    # Brier / ROC-AUC are defined on probability-like scores.
    upper = max(float(observed.max()) * 2.0, threshold * 2.0, 1e-6)
    predicted_prob = np.clip(predicted, 0.0, upper) / upper
    return {
        "rmse": rmse(observed, predicted),
        "mae": mae(observed, predicted),
        "nse": nse(observed, predicted),
        "brier": brier_score(observed_binary, predicted_prob),
        "roc_auc": (
            roc_auc(observed_binary, predicted_prob) if 0 < observed_binary.sum() < observed_binary.size else math.nan
        ),
        "ece": (
            expected_calibration_error(observed_binary, predicted_prob)
            if 0 < observed_binary.sum() < observed_binary.size
            else math.nan
        ),
    }


def _predict_pinn_ensemble(
    checkpoint_paths: list[Path],
    lons: np.ndarray,
    lats: np.ndarray,
    ts_normalised: np.ndarray,
    bbox: tuple[float, float, float, float],
) -> tuple[np.ndarray, np.ndarray]:
    """Mean and standard deviation across an ensemble of PINN checkpoints."""
    preds = [
        _predict_pinn(ckpt, lons, lats, ts_normalised, bbox) for ckpt in checkpoint_paths
    ]
    stack = np.stack(preds, axis=0)
    return stack.mean(axis=0), stack.std(axis=0)


def _predict_fno_ensemble(
    checkpoint_paths: list[Path],
    forcing_path: Path,
    lons: np.ndarray,
    lats: np.ndarray,
    ts_normalised: np.ndarray,
    bbox: tuple[float, float, float, float],
) -> np.ndarray | None:
    """Mean FNO prediction at observation locations.

    Loads each FNO checkpoint, advances it on the forcing snapshot
    nearest each report's timestamp, then interpolates the predicted
    field at the report's grid cell.  Returns ``None`` if no
    checkpoints are present.
    """
    try:
        import torch
        import torch.nn.functional as F

        from tideguard_ml.fno import load_fno_checkpoint
    except ImportError:
        return None
    if not checkpoint_paths:
        return None
    forcing = np.load(forcing_path)
    u_o, v_o = forcing["u_ocean"], forcing["v_ocean"]
    u_w, v_w = forcing["u_wind"], forcing["v_wind"]
    nt = u_o.shape[0]

    def _resample(a: np.ndarray) -> np.ndarray:
        ten = torch.from_numpy(a).float().unsqueeze(1)
        ten = F.interpolate(ten, size=(32, 32), mode="bilinear", align_corners=False)
        return ten.squeeze(1).numpy()
    u_o, v_o = _resample(u_o), _resample(v_o)
    u_w, v_w = _resample(u_w), _resample(v_w)
    inputs_np = np.stack([u_o, v_o, u_w, v_w], axis=1)
    inputs_t = torch.from_numpy(inputs_np).float()
    preds_per_member = []
    for ckpt in checkpoint_paths:
        model = load_fno_checkpoint(ckpt)
        with torch.no_grad():
            out = model(inputs_t).numpy()  # (nt, 32, 32)
        preds_per_member.append(out)
    field = np.stack(preds_per_member, axis=0).mean(axis=0)  # (nt, 32, 32)
    lon_min, lat_min, lon_max, lat_max = bbox
    obs_pred = np.zeros_like(lons, dtype=np.float64)
    for i, (lo, la, tn) in enumerate(zip(lons, lats, ts_normalised)):
        ti = min(int(tn * nt), nt - 1)
        gx = min(31, max(0, int((lo - lon_min) / max(lon_max - lon_min, 1e-9) * 32)))
        gy = min(31, max(0, int((la - lat_min) / max(lat_max - lat_min, 1e-9) * 32)))
        obs_pred[i] = field[ti, gy, gx]
    return obs_pred


def run_validation(
    csv: Path,
    checkpoint: Path,
    bbox: tuple[float, float, float, float],
    threshold_quantile: float = 0.9,
    bootstrap_replicates: int = 500,
    horizon_for_dm: int = 1,
    ensemble_checkpoints: list[Path] | None = None,
    fno_checkpoints: list[Path] | None = None,
    forcing_path: Path | None = None,
) -> ValidationReport:
    """Run the full validation harness.

    Parameters
    ----------
    csv : observations CSV.
    checkpoint : a single PINN checkpoint (kept for back-compat).
    ensemble_checkpoints : optional list of PINN checkpoints.  When
        provided, the ``pinn`` metric is computed against the ensemble
        mean and ``ensemble_std`` is included in the notes.
    fno_checkpoints : optional list of FNO checkpoints.  When provided
        the report also includes ``metrics['fno']`` and the BMA
        prediction (``metrics['bma']``) is computed.
    forcing_path : required when ``fno_checkpoints`` is non-empty.
    """
    lons, lats, ts, c = _read_csv(csv)
    lons, lats, ts, c = _filter_bbox(lons, lats, ts, c, bbox)

    t_min = float(ts.min())
    t_max = float(ts.max())
    t_span = max(t_max - t_min, 1.0)
    ts_norm = (ts - t_min) / t_span

    if ensemble_checkpoints:
        pinn_pred, pinn_std = _predict_pinn_ensemble(ensemble_checkpoints, lons, lats, ts_norm, bbox)
    else:
        pinn_pred = _predict_pinn(checkpoint, lons, lats, ts_norm, bbox)
        pinn_std = np.zeros_like(pinn_pred)
    persistence_pred = _predict_persistence(c)
    climatology_pred = _predict_climatology(c, ts_norm)

    fno_pred = None
    if fno_checkpoints and forcing_path is not None and Path(forcing_path).exists():
        try:
            fno_pred = _predict_fno_ensemble(fno_checkpoints, Path(forcing_path), lons, lats, ts_norm, bbox)
        except Exception as exc:  # pragma: no cover
            print(f"[fno_eval] failed: {exc}; skipping FNO baseline")
            fno_pred = None

    threshold = float(np.quantile(c, threshold_quantile))

    metrics = {
        "pinn": _build_metrics(c, pinn_pred, threshold),
        "persistence": _build_metrics(c, persistence_pred, threshold),
        "climatology": _build_metrics(c, climatology_pred, threshold),
    }

    bma_pred = None
    if fno_pred is not None:
        metrics["fno"] = _build_metrics(c, fno_pred, threshold)
        from tideguard_ml.uq import bma_predict, estimate_log_marginal
        member_preds = np.stack([pinn_pred, fno_pred, climatology_pred], axis=0)
        log_marginals = np.array(
            [
                estimate_log_marginal(c, pinn_pred),
                estimate_log_marginal(c, fno_pred),
                estimate_log_marginal(c, climatology_pred),
            ]
        )
        bma_pred, bma_weights = bma_predict(member_preds, log_marginals)
        metrics["bma"] = _build_metrics(c, bma_pred, threshold)
        metrics["bma_weights"] = {
            "pinn": float(bma_weights[0]),
            "fno": float(bma_weights[1]),
            "climatology": float(bma_weights[2]),
        }

    sq_pinn = (c - pinn_pred) ** 2
    sq_pers = (c - persistence_pred) ** 2
    sq_clim = (c - climatology_pred) ** 2

    dm_pinn_vs_persistence = diebold_mariano(sq_pinn, sq_pers, h=horizon_for_dm)
    dm_pinn_vs_climatology = diebold_mariano(sq_pinn, sq_clim, h=horizon_for_dm)
    bootstrap_pinn_vs_persistence = bootstrap_rmse_ci(c, pinn_pred, persistence_pred, n_replicates=bootstrap_replicates)
    bootstrap_pinn_vs_climatology = bootstrap_rmse_ci(c, pinn_pred, climatology_pred, n_replicates=bootstrap_replicates)

    statistical_tests = {
        "dm_pinn_vs_persistence": asdict(dm_pinn_vs_persistence),
        "dm_pinn_vs_climatology": asdict(dm_pinn_vs_climatology),
        "bootstrap_pinn_vs_persistence": asdict(bootstrap_pinn_vs_persistence),
        "bootstrap_pinn_vs_climatology": asdict(bootstrap_pinn_vs_climatology),
    }
    if bma_pred is not None:
        sq_bma = (c - bma_pred) ** 2
        statistical_tests["dm_bma_vs_persistence"] = asdict(
            diebold_mariano(sq_bma, sq_pers, h=horizon_for_dm)
        )

    notes = [
        f"observations after bbox filter: {int(c.size)}",
        f"threshold @ q={threshold_quantile:.2f}: {threshold:.4f}",
        "p_value < 0.05 indicates a statistically significant skill difference",
        "bootstrap CI not crossing zero indicates a significant difference at the 5% level",
    ]
    if ensemble_checkpoints:
        notes.append(
            f"PINN ensemble: {len(ensemble_checkpoints)} members; mean std={float(pinn_std.mean()):.4f}"
        )
    if fno_checkpoints:
        notes.append(f"FNO ensemble: {len(fno_checkpoints)} members; BMA across PINN+FNO+climatology")
    return ValidationReport(
        csv=str(csv),
        n_observations=int(c.size),
        bbox=list(bbox),
        threshold_quantile=float(threshold_quantile),
        threshold_value=float(threshold),
        metrics=metrics,
        statistical_tests=statistical_tests,
        notes=notes,
    )


def _parse_bbox(s: str) -> tuple[float, float, float, float]:
    parts = [float(x) for x in s.split(",")]
    if len(parts) != 4:
        raise SystemExit("--bbox must be lon_min,lat_min,lon_max,lat_max")
    return (parts[0], parts[1], parts[2], parts[3])


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate PINN against a CSV of real observations")
    parser.add_argument(
        "--csv", type=str, required=True, help="Observations CSV (lon,lat,ts_seconds,concentration[,source,license])"
    )
    parser.add_argument("--checkpoint", type=str, required=True, help="PINN checkpoint .pt")
    parser.add_argument(
        "--bbox", type=str, default="27,40,42,47", help="lon_min,lat_min,lon_max,lat_max (default: Black Sea)"
    )
    parser.add_argument("--threshold-quantile", type=float, default=0.9)
    parser.add_argument("--bootstrap-replicates", type=int, default=500)
    parser.add_argument(
        "--out",
        type=str,
        default="reports/real_validation_latest.json",
        help="Output JSON path (relative to apps/ml)",
    )
    args = parser.parse_args()

    report = run_validation(
        csv=Path(args.csv),
        checkpoint=Path(args.checkpoint),
        bbox=_parse_bbox(args.bbox),
        threshold_quantile=args.threshold_quantile,
        bootstrap_replicates=args.bootstrap_replicates,
    )

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = Path(__file__).resolve().parents[3] / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(asdict(report), indent=2))

    print(f"Real-data validation written to {out_path}")
    print(json.dumps(report.metrics, indent=2))
    if os.environ.get("CI") != "true":
        print("statistical tests:")
        print(json.dumps(report.statistical_tests, indent=2))


if __name__ == "__main__":
    main()
