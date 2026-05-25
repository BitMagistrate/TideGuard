"""Active-learning citizen tasking endpoints (TASK-023).

Derives "go take a photo of this beach" micro-tasks from grid cells where the
exceedance map has both high probability and high relative uncertainty. The
heuristic stays local (no ML extra inference) so we can re-use the cached
exceedance response.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from tideguard_api.services.inference import predict_exceedance

router = APIRouter(prefix="/tasking", tags=["tasking"])


@router.get("/citizen")
def citizen_tasks(
    bbox: str = Query("37.05,44.78,37.55,45.10", description="lon_min,lat_min,lon_max,lat_max"),
    horizon: int = Query(3, ge=1, le=14),
    top_k: int = Query(5, ge=1, le=20),
) -> dict:
    try:
        lon_min, lat_min, lon_max, lat_max = (float(x) for x in bbox.split(","))
    except Exception as exc:
        raise HTTPException(400, f"Invalid bbox: {exc}") from exc
    if not (lon_min < lon_max and lat_min < lat_max):
        raise HTTPException(400, "Invalid bbox ordering")

    response = predict_exceedance(
        lon_min=lon_min,
        lon_max=lon_max,
        lat_min=lat_min,
        lat_max=lat_max,
        horizon_days=horizon,
        quantile=0.8,
    )
    # We rank cells by `probability * (1 - probability)` — the highest-entropy
    # cells (closest to 0.5 probability) are the most informative for the
    # next round of training. This is the classic active-learning criterion.
    ranked = sorted(response.cells, key=lambda c: -(c.probability * (1.0 - c.probability)))[:top_k]
    return {
        "model_version": response.model_version,
        "tasks": [
            {
                "lat": c.lat,
                "lng": c.lng,
                "probability": c.probability,
                "rationale": "high model uncertainty — a photo here will sharpen the next forecast",
            }
            for c in ranked
        ],
    }
