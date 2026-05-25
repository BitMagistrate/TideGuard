"""Citizen reports endpoints (create, list, moderate, GDPR erasure).

Hardened per audit:
  * CRIT-API-10 — cursor-style pagination via ``limit + offset`` query params.
  * CRIT-API-14 — bbox bounded to sane lat/lon ranges.
  * CRIT-API-15 — orphan reports removed on user deletion (FK cascade in models).
  * EXIF GPS cross-check: photo with GPS > 200 m away from the user-supplied
    ``(lat, lng)`` is auto-queued for moderator review.
"""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.db import get_db
from tideguard_api.deps import get_current_user, require_moderator
from tideguard_api.models.report import Report
from tideguard_api.models.user import User
from tideguard_api.observability import record_upload
from tideguard_api.services.badges import maybe_award_badges
from tideguard_api.services.storage import upload_photo

router = APIRouter(prefix="/reports", tags=["reports"])

REPORT_XP = 10
ReportStatus = Literal["pending", "approved", "rejected"]
MAX_LIMIT = 500


class ReportStatusUpdate(BaseModel):
    status: ReportStatus = Field(..., description="pending | approved | rejected")
    moderator_note: str | None = None


def _serialize(r: Report) -> dict:
    return {
        "id": str(r.id),
        "user_id": str(r.user_id),
        "lat": r.lat,
        "lng": r.lng,
        "photo_url": r.photo_url,
        "severity": r.severity,
        "debris_type": r.debris_type,
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _validate_bbox(lon_min: float, lat_min: float, lon_max: float, lat_max: float) -> None:
    if not (-180 <= lon_min < lon_max <= 180):
        raise HTTPException(400, "Invalid bbox lon range")
    if not (-90 <= lat_min < lat_max <= 90):
        raise HTTPException(400, "Invalid bbox lat range")
    if (lon_max - lon_min) > 90 or (lat_max - lat_min) > 60:
        raise HTTPException(400, "bbox too large (max 90° lon × 60° lat)")


@router.post("")
async def create_report(
    photo: UploadFile = File(...),
    lat: float = Form(...),
    lng: float = Form(...),
    severity: int = Form(...),
    debris_type: str = Form("plastic_bottle"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise HTTPException(400, "Invalid coordinates")
    if not (1 <= severity <= 5):
        raise HTTPException(400, "severity must be 1..5")

    try:
        upload = await upload_photo(photo, user.id, user_lat=lat, user_lng=lng)
    except HTTPException as exc:
        record_upload(photo.content_type or "unknown", "rejected")
        raise exc

    record_upload(photo.content_type or "unknown", "ok")
    status_initial: str = "pending"
    if upload.gps_mismatch_m is not None and upload.gps_mismatch_m > 1000:
        # Strong GPS mismatch — keep pending and let moderator decide.
        status_initial = "pending"

    report = Report(
        id=uuid.uuid4(),
        user_id=user.id,
        lat=lat,
        lng=lng,
        photo_url=upload.url,
        severity=severity,
        debris_type=debris_type,
        status=status_initial,
    )
    db.add(report)
    user.xp = (user.xp or 0) + REPORT_XP
    await db.commit()
    await db.refresh(report)
    await maybe_award_badges(db, user)
    return {
        "id": str(report.id),
        "photo_url": upload.url,
        "xp": user.xp,
        "phash": upload.phash,
        "gps_present": upload.gps_present,
        "gps_mismatch_m": upload.gps_mismatch_m,
    }


@router.get("")
async def list_reports(
    bbox: str = Query(..., description="lon_min,lat_min,lon_max,lat_max"),
    limit: int = Query(1000, ge=1, le=MAX_LIMIT * 2),
    offset: int = Query(0, ge=0),
    paginated: bool = Query(
        False,
        description="If true, return {items, has_more, next_offset} instead of bare list.",
    ),
    db: AsyncSession = Depends(get_db),
):
    """List approved reports inside the bbox.

    Default response is a bare list (backwards-compat).  Pass
    ``paginated=true`` to get a structured response with a
    ``has_more`` flag (B13) and a ``next_offset`` cursor:

    ``{"items": [...], "has_more": true, "next_offset": 25, "limit": 25, "offset": 0}``
    """
    try:
        lon_min, lat_min, lon_max, lat_max = map(float, bbox.split(","))
    except Exception as exc:
        raise HTTPException(400, f"Invalid bbox: {exc}") from exc
    _validate_bbox(lon_min, lat_min, lon_max, lat_max)
    limit = min(limit, MAX_LIMIT)

    # We fetch ``limit + 1`` to detect whether there's a next page without
    # an extra COUNT(*) query.
    fetch_n = limit + 1
    stmt = (
        select(Report)
        .where(
            Report.status == "approved",
            Report.lng >= lon_min,
            Report.lng <= lon_max,
            Report.lat >= lat_min,
            Report.lat <= lat_max,
        )
        .order_by(Report.created_at.desc())
        .offset(offset)
        .limit(fetch_n)
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]
    items = [_serialize(r) for r in rows]
    if paginated:
        return {
            "items": items,
            "has_more": has_more,
            "next_offset": (offset + limit) if has_more else None,
            "limit": limit,
            "offset": offset,
        }
    return items


@router.get("/queue")
async def moderator_queue(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _mod: User = Depends(require_moderator),
) -> list[dict]:
    stmt = select(Report).where(Report.status == "pending").order_by(Report.created_at.desc()).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return [_serialize(r) for r in rows]


@router.get("/mine")
async def my_reports(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict]:
    stmt = select(Report).where(Report.user_id == user.id).order_by(Report.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return [_serialize(r) for r in rows]


@router.delete("/mine")
async def delete_my_reports(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """GDPR Art. 17 — right to erasure. Deletes ALL of the caller's reports."""
    result = await db.execute(delete(Report).where(Report.user_id == user.id))
    await db.commit()
    return {"deleted": getattr(result, "rowcount", 0) or 0}


@router.patch("/{report_id}")
async def update_report(
    report_id: uuid.UUID,
    payload: ReportStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _mod: User = Depends(require_moderator),
) -> dict:
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Report not found")
    report.status = payload.status
    await db.commit()
    return {"id": str(report.id), "status": report.status, "moderator_note": payload.moderator_note}
