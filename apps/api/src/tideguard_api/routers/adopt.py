"""Adopt-a-Beach endpoints (§6)."""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.db import get_db
from tideguard_api.deps import get_current_user
from tideguard_api.models.adoption import Adoption
from tideguard_api.models.beach_segment import BeachSegment
from tideguard_api.models.user import User
from tideguard_api.schemas.adopt import (
    AdoptionOut,
    BeachSegmentDetail,
    BeachSegmentOut,
    CheckoutRequest,
    ReserveRequest,
    ReserveResponse,
    TransferRequest,
)
from tideguard_api.services.billing_gateway import get_billing_gateway
from tideguard_api.settings import get_settings

router = APIRouter(prefix="/adopt", tags=["adopt"])


def _seg_out(s: BeachSegment) -> BeachSegmentOut:
    return BeachSegmentOut(
        id=str(s.id),
        slug=s.slug,
        region_id=str(s.region_id) if s.region_id else None,
        midpoint_lat=s.midpoint_lat,
        midpoint_lng=s.midpoint_lng,
        length_m=s.length_m,
        display_name=s.display_name,
        status=s.status,
    )


@router.get("/segments", response_model=list[BeachSegmentOut])
async def list_segments(
    bbox: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[BeachSegmentOut]:
    stmt = select(BeachSegment).order_by(BeachSegment.slug)
    if bbox:
        try:
            parts = [float(p) for p in bbox.split(",")]
            if len(parts) != 4:
                raise ValueError("expected lon_min,lat_min,lon_max,lat_max")
            lon_min, lat_min, lon_max, lat_max = parts
            stmt = stmt.where(
                BeachSegment.midpoint_lng >= lon_min,
                BeachSegment.midpoint_lng <= lon_max,
                BeachSegment.midpoint_lat >= lat_min,
                BeachSegment.midpoint_lat <= lat_max,
            )
        except ValueError as exc:
            raise HTTPException(400, f"bad bbox: {exc}") from exc
    if status:
        stmt = stmt.where(BeachSegment.status == status)
    rows = await db.execute(stmt.limit(2000))
    return [_seg_out(s) for s in rows.scalars()]


@router.get("/segments/{slug}", response_model=BeachSegmentDetail)
async def get_segment(slug: str, db: AsyncSession = Depends(get_db)) -> BeachSegmentDetail:
    res = await db.execute(select(BeachSegment).where(BeachSegment.slug == slug))
    seg = res.scalar_one_or_none()
    if seg is None:
        raise HTTPException(404, "segment not found")
    base = _seg_out(seg).model_dump()
    return BeachSegmentDetail(**base, geom_wkt=seg.geom_wkt, history=[])


@router.post("/reserve", response_model=ReserveResponse)
async def reserve(
    payload: ReserveRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReserveResponse:
    try:
        seg_uuid = uuid.UUID(payload.segment_id)
    except ValueError as exc:
        raise HTTPException(400, "invalid segment_id") from exc
    res = await db.execute(select(BeachSegment).where(BeachSegment.id == seg_uuid))
    seg = res.scalar_one_or_none()
    if seg is None:
        raise HTTPException(404, "segment not found")
    if seg.status != "available":
        raise HTTPException(409, f"segment status is {seg.status}")
    seg.status = "reserved"
    await db.commit()
    return ReserveResponse(
        segment_id=str(seg.id),
        expires_at=datetime.now(UTC) + timedelta(minutes=30),
        token=secrets.token_hex(16),
    )


@router.post("/checkout", status_code=201)
async def checkout(
    payload: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    settings = get_settings()
    # enforce max active adoptions per user
    active_rows = await db.execute(
        select(func.count(Adoption.id)).where(Adoption.adopter_user_id == user.id, Adoption.status == "active")
    )
    active_count = active_rows.scalar() or 0
    if active_count >= settings.adopt_max_active_per_user:
        raise HTTPException(409, "max active adoptions per user reached")

    try:
        seg_uuid = uuid.UUID(payload.segment_id)
    except ValueError as exc:
        raise HTTPException(400, "invalid segment_id") from exc
    res = await db.execute(select(BeachSegment).where(BeachSegment.id == seg_uuid))
    seg = res.scalar_one_or_none()
    if seg is None:
        raise HTTPException(404, "segment not found")
    if seg.status == "adopted":
        raise HTTPException(409, "segment already adopted")

    adoption = Adoption(
        id=uuid.uuid4(),
        segment_id=seg.id,
        adopter_user_id=user.id,
        tier=payload.tier,
        starts_at=datetime.now(UTC),
        ends_at=(datetime.now(UTC) + timedelta(days=365)) if payload.period == "yearly" else (
            datetime.now(UTC) + timedelta(days=30)
        ),
        status="active",
        display_name=payload.display_name,
        show_publicly=payload.show_publicly,
    )
    seg.status = "adopted"
    db.add(adoption)
    await db.commit()
    await db.refresh(adoption)

    gateway = get_billing_gateway()
    checkout_url = gateway.create_checkout_session(
        customer_id=f"adopt_user_{user.id}",
        price_id=f"price_{payload.tier}_{payload.period}",
        success_url=f"https://tideguard.app/dashboard/adoptions?adoption_id={adoption.id}",
        cancel_url=f"https://tideguard.app/adopt-a-beach/{seg.slug}",
    )
    return {
        "adoption_id": str(adoption.id),
        "segment_slug": seg.slug,
        "checkout_url": checkout_url,
        "status": "pending_payment",
    }


@router.get("/mine", response_model=list[AdoptionOut])
async def my_adoptions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AdoptionOut]:
    rows = await db.execute(
        select(Adoption, BeachSegment)
        .join(BeachSegment, BeachSegment.id == Adoption.segment_id)
        .where(Adoption.adopter_user_id == user.id)
        .order_by(Adoption.created_at.desc())
    )
    out = []
    for adoption, seg in rows.all():
        out.append(
            AdoptionOut(
                id=str(adoption.id),
                segment_id=str(adoption.segment_id),
                segment_slug=seg.slug,
                tier=adoption.tier,
                starts_at=adoption.starts_at,
                ends_at=adoption.ends_at,
                status=adoption.status,
                display_name=adoption.display_name,
                show_publicly=adoption.show_publicly,
            )
        )
    return out


@router.delete("/{adoption_id}", status_code=204)
async def cancel_adoption(
    adoption_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    res = await db.execute(select(Adoption).where(Adoption.id == adoption_id, Adoption.adopter_user_id == user.id))
    row = res.scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "adoption not found")
    row.status = "cancelled"
    seg = await db.get(BeachSegment, row.segment_id)
    if seg is not None:
        seg.status = "available"
    await db.commit()


@router.post("/{adoption_id}/transfer", response_model=AdoptionOut)
async def transfer_adoption(
    adoption_id: uuid.UUID,
    payload: TransferRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AdoptionOut:
    res = await db.execute(select(Adoption).where(Adoption.id == adoption_id, Adoption.adopter_user_id == user.id))
    row = res.scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "adoption not found")
    new_user_res = await db.execute(select(User).where(User.email == payload.new_email))
    new_user = new_user_res.scalar_one_or_none()
    if new_user is None:
        raise HTTPException(404, "recipient is not a TideGuard user yet")
    row.adopter_user_id = new_user.id
    await db.commit()
    seg = await db.get(BeachSegment, row.segment_id)
    return AdoptionOut(
        id=str(row.id),
        segment_id=str(row.segment_id),
        segment_slug=seg.slug if seg else "?",
        tier=row.tier,
        starts_at=row.starts_at,
        ends_at=row.ends_at,
        status=row.status,
        display_name=row.display_name,
        show_publicly=row.show_publicly,
    )
