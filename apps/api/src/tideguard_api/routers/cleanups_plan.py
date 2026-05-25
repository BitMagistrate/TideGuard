"""Cleanup routing endpoint — VRP over the latest exceedance map (TASK-008)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from tideguard_api.services.inference import predict_exceedance
from tideguard_api.services.routing import hotspots_from_exceedance, plan_cleanup

router = APIRouter(prefix="/cleanups", tags=["cleanups"])


class PlanRequest(BaseModel):
    bbox: tuple[float, float, float, float] = Field(
        ..., description="(lon_min, lat_min, lon_max, lat_max)"
    )
    horizon_days: int = Field(3, ge=1, le=14)
    n_teams: int = Field(4, ge=1, le=50)
    budget_minutes: int = Field(180, ge=30, le=24 * 60)
    start: tuple[float, float] = Field(
        ..., description="(lon, lat) — coordinator depot / staging point"
    )
    speed_kmh: float = Field(5.0, ge=1.0, le=80.0)
    quantile: float = Field(0.85, ge=0.5, le=0.99)
    top_k: int = Field(25, ge=3, le=200)


@router.post("/plan")
def plan(payload: PlanRequest) -> dict:
    lon_min, lat_min, lon_max, lat_max = payload.bbox
    if not (lon_min < lon_max and lat_min < lat_max):
        raise HTTPException(400, "Invalid bbox ordering")
    if not (-180 <= lon_min and lon_max <= 180 and -90 <= lat_min and lat_max <= 90):
        raise HTTPException(400, "Bbox out of geographic range")

    exceedance = predict_exceedance(
        lon_min=lon_min,
        lon_max=lon_max,
        lat_min=lat_min,
        lat_max=lat_max,
        horizon_days=payload.horizon_days,
        quantile=payload.quantile,
    )
    hotspots = hotspots_from_exceedance(exceedance, top_k=payload.top_k, min_probability=0.5)
    plan_geojson = plan_cleanup(
        hotspots=hotspots,
        n_teams=payload.n_teams,
        budget_min=payload.budget_minutes,
        start=payload.start,
        speed_kmh=payload.speed_kmh,
    )
    plan_geojson["bbox"] = list(payload.bbox)
    plan_geojson["horizon_days"] = payload.horizon_days
    plan_geojson["model_version"] = exceedance.model_version
    return plan_geojson
