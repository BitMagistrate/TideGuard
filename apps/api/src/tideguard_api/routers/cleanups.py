"""Cleanups endpoints — events with collected mass + photos.

Hardened per audit:
  * CRIT-API-16 — POLYGON WKT validated through Shapely (when available) instead
    of `.+` regex; in pure-Python fallback we still tighten the regex and
    parse coordinates.
  * `kg_collected` capped at a sane upper bound (50,000 kg per event).
"""

from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.db import get_db
from tideguard_api.deps import get_current_user
from tideguard_api.models.cleanup import Cleanup
from tideguard_api.models.user import User
from tideguard_api.services.badges import maybe_award_badges

router = APIRouter(prefix="/cleanups", tags=["cleanups"])

CLEANUP_XP = 100
KG_MAX = 50_000.0

# Tighter regex: at least one ring, with at least 4 numeric coordinate pairs.
_WKT_POLYGON = re.compile(
    r"^POLYGON\s*\(\(\s*(?:-?\d+(?:\.\d+)?\s+-?\d+(?:\.\d+)?\s*,\s*){3,}-?\d+(?:\.\d+)?\s+-?\d+(?:\.\d+)?\s*\)\)$",
    re.IGNORECASE | re.DOTALL,
)


def _validate_wkt_polygon(wkt: str) -> None:
    wkt_stripped = wkt.strip()
    try:  # pragma: no cover — exercised only when Shapely is available.
        from shapely import wkt as shapely_wkt
        from shapely.geometry import Polygon

        geom = shapely_wkt.loads(wkt_stripped)
        if not isinstance(geom, Polygon):
            raise HTTPException(400, "geom_wkt must be a POLYGON")
        if geom.is_empty or not geom.is_valid:
            raise HTTPException(400, "geom_wkt is empty or invalid")
        ring = geom.exterior
        if ring is None or len(list(ring.coords)) < 4:
            raise HTTPException(400, "POLYGON exterior ring must have ≥4 coords")
        bounds = geom.bounds
        if not (-180 <= bounds[0] <= 180 and -180 <= bounds[2] <= 180):
            raise HTTPException(400, "POLYGON lon out of [-180,180]")
        if not (-90 <= bounds[1] <= 90 and -90 <= bounds[3] <= 90):
            raise HTTPException(400, "POLYGON lat out of [-90,90]")
        return
    except HTTPException:
        raise
    except ModuleNotFoundError:
        pass
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"Cannot parse POLYGON WKT: {exc}") from exc
    # Shapely-less fallback — at least enforce the structural regex above.
    if not _WKT_POLYGON.match(wkt_stripped):
        raise HTTPException(400, "geom_wkt must be a POLYGON WKT")


class CleanupCreate(BaseModel):
    geom_wkt: str = Field(..., description="POLYGON WKT, EPSG:4326")
    kg_collected: float = Field(..., ge=0, le=KG_MAX)
    participants: int = Field(..., ge=1, le=10_000)
    before_photo: str | None = None
    after_photo: str | None = None


@router.post("")
async def create_cleanup(
    payload: CleanupCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    _validate_wkt_polygon(payload.geom_wkt)
    cleanup = Cleanup(
        id=uuid.uuid4(),
        user_id=user.id,
        geom_wkt=payload.geom_wkt,
        kg_collected=payload.kg_collected,
        participants=payload.participants,
        before_photo=payload.before_photo,
        after_photo=payload.after_photo,
    )
    db.add(cleanup)
    user.xp = (user.xp or 0) + CLEANUP_XP
    await db.commit()
    await db.refresh(cleanup)
    await maybe_award_badges(db, user)
    return {"id": str(cleanup.id), "xp": user.xp}


@router.get("/stats")
async def cleanup_stats(db: AsyncSession = Depends(get_db)) -> dict:
    total_kg = (await db.execute(select(func.coalesce(func.sum(Cleanup.kg_collected), 0.0)))).scalar() or 0.0
    total_participants = (await db.execute(select(func.coalesce(func.sum(Cleanup.participants), 0)))).scalar() or 0
    total_events = (await db.execute(select(func.count(Cleanup.id)))).scalar() or 0
    return {
        "kg_collected": float(total_kg),
        "participants": int(total_participants),
        "events": int(total_events),
        "cleanups": int(total_events),
    }


@router.get("")
async def list_cleanups(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    stmt = select(Cleanup).order_by(Cleanup.created_at.desc()).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": str(c.id),
            "user_id": str(c.user_id),
            "geom_wkt": c.geom_wkt,
            "kg_collected": c.kg_collected,
            "participants": c.participants,
            "before_photo": c.before_photo,
            "after_photo": c.after_photo,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in rows
    ]
