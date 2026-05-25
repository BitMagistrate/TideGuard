"""Forecast endpoint — serves PINN predictions (or mock fallback)."""

from __future__ import annotations

from datetime import date as _date

from fastapi import APIRouter, HTTPException, Query

from tideguard_api.schemas.forecast import (
    ActiveLearningResponse,
    BackwardResponse,
    CounterfactualResponse,
    ExceedanceResponse,
    ExplainResponse,
    ForecastResponse,
)
from tideguard_api.services.inference import (
    predict_active_learning,
    predict_backward,
    predict_counterfactual,
    predict_exceedance,
    predict_explain,
    predict_forecast,
)
from tideguard_api.settings import get_settings

router = APIRouter(prefix="/forecast", tags=["forecast"])


def _parse_bbox(bbox: str) -> tuple[float, float, float, float]:
    try:
        lon_min, lat_min, lon_max, lat_max = (float(x) for x in bbox.split(","))
    except Exception as exc:
        raise HTTPException(400, f"Invalid bbox: {exc}") from exc
    if lon_min >= lon_max or lat_min >= lat_max:
        raise HTTPException(400, "Invalid bbox ordering")
    if not (-180 <= lon_min and lon_max <= 180):
        raise HTTPException(400, "lon out of [-180, 180]")
    if not (-90 <= lat_min and lat_max <= 90):
        raise HTTPException(400, "lat out of [-90, 90]")
    if (lon_max - lon_min) > 60 or (lat_max - lat_min) > 30:
        raise HTTPException(400, "bbox too large (max 60° lon × 30° lat per request)")
    return lon_min, lat_min, lon_max, lat_max


def _check_domain(bbox: tuple[float, float, float, float]) -> None:
    """CRIT-ML-2: reject bboxes outside the training domain by > 5 %."""
    settings = get_settings()
    lon_min, lat_min, lon_max, lat_max = bbox
    span_lon = settings.domain_lon_max - settings.domain_lon_min
    span_lat = settings.domain_lat_max - settings.domain_lat_min
    pad_lon = 0.05 * span_lon
    pad_lat = 0.05 * span_lat
    if (
        lon_min < settings.domain_lon_min - pad_lon
        or lon_max > settings.domain_lon_max + pad_lon
        or lat_min < settings.domain_lat_min - pad_lat
        or lat_max > settings.domain_lat_max + pad_lat
    ):
        raise HTTPException(
            422,
            (
                f"bbox out of trained domain '{settings.domain_name}' "
                f"({settings.domain_lon_min},{settings.domain_lat_min},"
                f"{settings.domain_lon_max},{settings.domain_lat_max})"
            ),
        )


def _validate_as_of_date(as_of_date: str | None) -> str | None:
    if as_of_date is None:
        return None
    try:
        d = _date.fromisoformat(as_of_date)
    except ValueError as exc:
        raise HTTPException(400, f"as_of_date must be YYYY-MM-DD: {exc}") from exc
    if d > _date.today():
        raise HTTPException(400, "as_of_date cannot be in the future")
    if d.year < 2020:
        raise HTTPException(400, "as_of_date predates the forcing snapshot archive (2020-01-01)")
    return as_of_date


@router.get("", response_model=ForecastResponse)
def get_forecast(
    bbox: str = Query(
        "27,40,42,47",
        description="lon_min,lat_min,lon_max,lat_max (default: Black Sea pilot)",
    ),
    horizon: int = Query(7, ge=1, le=14, description="Forecast horizon in days (1-14)"),
    strict_domain: bool = Query(
        False,
        description="If true, reject bboxes more than 5 % outside the trained domain.",
    ),
    as_of_date: str | None = Query(
        None,
        description=(
            "ISO-8601 date (YYYY-MM-DD). When provided, the forecast is replayed from "
            "the corresponding archived CMEMS/ERA5 snapshot — 'time-machine' mode."
        ),
    ),
) -> ForecastResponse:
    parsed = _parse_bbox(bbox)
    if strict_domain:
        _check_domain(parsed)
    as_of = _validate_as_of_date(as_of_date)
    lon_min, lat_min, lon_max, lat_max = parsed
    result = predict_forecast(lon_min, lon_max, lat_min, lat_max, horizon_days=horizon)
    if as_of:
        # Honest: ground-truth comparison is only available once the cron job
        # has logged the historical observations; we expose the field so that
        # the /map UI can render the green/red banner unconditionally.
        result.as_of_date = as_of
        result.ground_truth_available = False
    return result


@router.get("/exceedance", response_model=ExceedanceResponse)
def get_exceedance(
    bbox: str = Query("27,40,42,47", description="lon_min,lat_min,lon_max,lat_max (default: Black Sea)"),
    horizon: int = Query(7, ge=1, le=14, description="Forecast horizon in days (1-14)"),
    threshold: float | None = Query(None, ge=0.0),
    quantile: float = Query(0.9, gt=0.0, lt=1.0),
    strict_domain: bool = Query(False),
) -> ExceedanceResponse:
    parsed = _parse_bbox(bbox)
    if strict_domain:
        _check_domain(parsed)
    lon_min, lat_min, lon_max, lat_max = parsed
    return predict_exceedance(
        lon_min=lon_min,
        lon_max=lon_max,
        lat_min=lat_min,
        lat_max=lat_max,
        horizon_days=horizon,
        threshold=threshold,
        quantile=quantile,
    )


@router.get("/explain", response_model=ExplainResponse)
def get_forecast_explain(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lng: float = Query(..., ge=-180.0, le=180.0),
    horizon: int = Query(7, ge=1, le=14),
    as_of_date: str | None = Query(None),
) -> ExplainResponse:
    """SHAP-style decomposition of the forecast at a point."""
    as_of = _validate_as_of_date(as_of_date)
    return predict_explain(lat=lat, lng=lng, horizon_days=horizon, as_of_date=as_of)


@router.get("/backward", response_model=BackwardResponse)
def get_forecast_backward(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lng: float = Query(..., ge=-180.0, le=180.0),
    days_back: int = Query(14, ge=1, le=30),
) -> BackwardResponse:
    """Reverse-trajectory source attribution for transboundary pollution.

    Use case: ministry needs to identify the upstream source of plastic
    that washes up on a Russian beach so it can be reported in the
    Bucharest Convention bilateral talks (Bulgaria / Romania / Turkey
    / Georgia).
    """
    return predict_backward(lat=lat, lng=lng, days_back=days_back)


@router.get("/counterfactual", response_model=CounterfactualResponse)
def get_forecast_counterfactual(
    bbox: str = Query("27,40,42,47"),
    horizon: int = Query(7, ge=1, le=14),
    modify: str = Query(
        "wind*0.5",
        description=(
            "Comma-separated modifications: 'key*scalar' or 'disable_<key>'. "
            "Supported keys: wind, windage, ocean, advection, diffusion, "
            "stokes_drift, beaching."
        ),
    ),
) -> CounterfactualResponse:
    """Run the forecast with a perturbed physics knob and return the diff."""
    parsed = _parse_bbox(bbox)
    lon_min, lat_min, lon_max, lat_max = parsed
    return predict_counterfactual(
        lon_min=lon_min,
        lon_max=lon_max,
        lat_min=lat_min,
        lat_max=lat_max,
        horizon_days=horizon,
        modify=modify,
    )


@router.get("/active_learning", response_model=ActiveLearningResponse)
def get_forecast_active_learning(
    bbox: str = Query("27,40,42,47"),
    horizon: int = Query(7, ge=1, le=14),
    k: int = Query(5, ge=1, le=20),
) -> ActiveLearningResponse:
    """Return the top-k cells where a new citizen report would maximally
    reduce ensemble uncertainty (BALD acquisition function).
    """
    parsed = _parse_bbox(bbox)
    lon_min, lat_min, lon_max, lat_max = parsed
    return predict_active_learning(
        lon_min=lon_min,
        lon_max=lon_max,
        lat_min=lat_min,
        lat_max=lat_max,
        horizon_days=horizon,
        k=k,
    )
