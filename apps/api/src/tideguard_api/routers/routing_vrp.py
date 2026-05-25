"""VRP planner endpoints — wraps the OR-Tools solver (§4.2.4)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.db import get_db
from tideguard_api.models.region import Region
from tideguard_api.schemas.b2g import VrpRequest, VrpResponse, VrpRoute, VrpStop
from tideguard_api.services.inference import predict_exceedance
from tideguard_api.services.vrp_solver import Hotspot, solve_vrp
from tideguard_api.settings import get_settings

router = APIRouter(prefix="/b2g/routing", tags=["b2g"])


@router.post("/solve", response_model=VrpResponse)
async def solve(payload: VrpRequest, db: AsyncSession = Depends(get_db)) -> VrpResponse:
    res = await db.execute(select(Region).where(Region.slug == payload.region))
    region = res.scalar_one_or_none()
    if region is None:
        raise HTTPException(404, f"unknown region {payload.region!r}")
    bbox = region.bbox
    exc = predict_exceedance(
        lon_min=bbox[0], lon_max=bbox[2], lat_min=bbox[1], lat_max=bbox[3],
        horizon_days=7, quantile=0.85,
    )
    top = sorted(exc.cells, key=lambda c: -c.probability)[: payload.hotspot_top_n]
    hotspots = [
        Hotspot(
            lat=c.lat, lng=c.lng, probability=c.probability,
            est_kg=max(10.0, c.probability * 50.0), hotspot_id=f"hp-{i + 1}",
        )
        for i, c in enumerate(top)
    ]
    depot = (
        (payload.depot_lat, payload.depot_lng)
        if payload.depot_lat is not None and payload.depot_lng is not None
        else ((bbox[1] + bbox[3]) / 2.0, (bbox[0] + bbox[2]) / 2.0)
    )
    settings = get_settings()
    result = solve_vrp(
        depot=depot,
        hotspots=hotspots,
        team_size=payload.team_size,
        capacity_kg=payload.capacity_kg_per_team,
        time_limit_ms=settings.or_tools_solver_time_limit_ms,
    )
    return VrpResponse(
        routes=[
            VrpRoute(
                team_id=r.team_id,
                stops=[
                    VrpStop(
                        seq=s.seq, lat=s.lat, lng=s.lng, hotspot_id=s.hotspot_id,
                        arrive=s.arrive, depart=s.depart, est_kg=s.est_kg, p_exceed=s.p_exceed,
                    )
                    for s in r.stops
                ],
                total_distance_km=r.total_distance_km,
                total_time_min=r.total_time_min,
                total_kg_est=r.total_kg_est,
            )
            for r in result.routes
        ],
        unassigned_hotspots=result.unassigned_hotspots,
        total_kg_est=result.total_kg_est,
        solver_status=result.solver_status,
        solve_time_ms=result.solve_time_ms,
    )
