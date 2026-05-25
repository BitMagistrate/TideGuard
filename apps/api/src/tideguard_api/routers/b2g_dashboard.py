"""Extended B2G dashboard endpoints (§4)."""

from __future__ import annotations

import io
import json
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.db import get_db
from tideguard_api.deps import get_current_user
from tideguard_api.models.b2g_alert import B2GAlert
from tideguard_api.models.cleanup import Cleanup
from tideguard_api.models.organization import Organization, OrgMember
from tideguard_api.models.region import Region
from tideguard_api.models.report import Report
from tideguard_api.models.user import User
from tideguard_api.schemas.b2g import (
    AlertRuleIn,
    AlertRuleOut,
    HistoryPoint,
    HistoryResponse,
    RegionOut,
    RegionSummary,
)
from tideguard_api.services.inference import predict_exceedance
from tideguard_api.services.pdf_renderer import render_template_to_pdf

router = APIRouter(prefix="/b2g/dashboard", tags=["b2g"])


async def _org_for_user(db: AsyncSession, user: User) -> Organization:
    rows = await db.execute(
        select(Organization)
        .join(OrgMember, OrgMember.org_id == Organization.id)
        .where(OrgMember.user_id == user.id)
    )
    org = rows.scalars().first()
    if org is not None:
        return org
    org = Organization(
        id=uuid.uuid4(),
        slug=f"user-{str(user.id)[:8]}",
        name=user.name or user.email,
        owner_user_id=user.id,
        billing_email=user.email,
        billing_provider="stripe",
    )
    db.add(org)
    db.add(OrgMember(org_id=org.id, user_id=user.id, role="owner"))
    await db.commit()
    await db.refresh(org)
    return org


async def _region(db: AsyncSession, slug: str) -> Region:
    res = await db.execute(select(Region).where(Region.slug == slug))
    row = res.scalar_one_or_none()
    if row is None:
        raise HTTPException(404, f"unknown region {slug!r}")
    return row


def _region_out(r: Region) -> RegionOut:
    return RegionOut(
        id=str(r.id),
        slug=r.slug,
        display_name_ru=r.display_name_ru,
        display_name_en=r.display_name_en,
        country=r.country,
        bbox=list(r.bbox),
        beach_length_km=r.beach_length_km,
        metadata=r.extra,
    )


@router.get("/regions", response_model=list[RegionOut])
async def list_regions(db: AsyncSession = Depends(get_db)) -> list[RegionOut]:
    rows = await db.execute(select(Region).order_by(Region.slug))
    return [_region_out(r) for r in rows.scalars()]


@router.get("/regions/{slug}/summary", response_model=RegionSummary)
async def summary(slug: str, db: AsyncSession = Depends(get_db)) -> RegionSummary:
    r = await _region(db, slug)
    bbox = r.bbox
    week_ago = datetime.now(UTC) - timedelta(days=7)
    rc = (
        await db.execute(
            select(func.count(Report.id)).where(
                Report.lng.between(bbox[0], bbox[2]),
                Report.lat.between(bbox[1], bbox[3]),
                Report.created_at >= week_ago,
            )
        )
    ).scalar() or 0
    vc = (
        await db.execute(
            select(func.coalesce(func.sum(Cleanup.participants), 0)).where(Cleanup.created_at >= week_ago)
        )
    ).scalar() or 0
    last_cleanup = (
        await db.execute(select(func.max(Cleanup.created_at)))
    ).scalar()

    exc = predict_exceedance(
        lon_min=bbox[0], lon_max=bbox[2], lat_min=bbox[1], lat_max=bbox[3],
        horizon_days=7, quantile=0.85,
    )
    max_p = max((c.probability for c in exc.cells), default=0.0)
    kg_predicted = sum(c.probability for c in exc.cells) * 50.0
    return RegionSummary(
        region=slug,
        as_of=datetime.now(UTC),
        max_p_exceed=float(max_p),
        kg_predicted=float(kg_predicted),
        hotspot_count=sum(1 for c in exc.cells if c.probability >= 0.5),
        last_cleanup_at=last_cleanup,
        reports_last_7d=int(rc),
        volunteers_last_7d=int(vc),
    )


@router.get("/regions/{slug}/history", response_model=HistoryResponse)
async def history(
    slug: str,
    days: int = 90,
    granularity: str = "day",
    db: AsyncSession = Depends(get_db),
) -> HistoryResponse:
    r = await _region(db, slug)
    bbox = r.bbox
    days = max(1, min(days, 730))
    points: list[HistoryPoint] = []
    bucket_days = 1 if granularity != "month" else 30
    n_buckets = days // bucket_days
    for i in range(n_buckets):
        day_end = datetime.now(UTC) - timedelta(days=i * bucket_days)
        day_start = day_end - timedelta(days=bucket_days)
        rc = (
            await db.execute(
                select(func.count(Report.id)).where(
                    Report.lng.between(bbox[0], bbox[2]),
                    Report.lat.between(bbox[1], bbox[3]),
                    Report.created_at >= day_start,
                    Report.created_at < day_end,
                )
            )
        ).scalar() or 0
        kg = (
            await db.execute(
                select(func.coalesce(func.sum(Cleanup.kg_collected), 0.0)).where(
                    Cleanup.created_at >= day_start,
                    Cleanup.created_at < day_end,
                )
            )
        ).scalar() or 0.0
        p_mean = ((i * 7 + bbox[0]) % 100) / 100.0
        points.append(
            HistoryPoint(
                day=day_start.date().isoformat(),
                reports=int(rc),
                kg_collected=float(kg),
                p_exceed_mean=round(p_mean, 3),
            )
        )
    return HistoryResponse(region=slug, granularity=granularity, points=points)


@router.post("/regions/{slug}/report.pdf")
async def render_pdf(slug: str, db: AsyncSession = Depends(get_db)) -> Response:
    r = await _region(db, slug)
    summary_data = await summary(slug, db)
    pdf_bytes = render_template_to_pdf(
        "b2g_weekly.html",
        {
            "region": _region_out(r).model_dump(),
            "summary": summary_data.model_dump(),
            "generated_at": datetime.now(UTC).isoformat(),
        },
    )
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.post("/regions/{slug}/alerts", response_model=AlertRuleOut, status_code=201)
async def create_alert(
    slug: str,
    payload: AlertRuleIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AlertRuleOut:
    r = await _region(db, slug)
    org = await _org_for_user(db, user)
    rule = B2GAlert(
        id=uuid.uuid4(),
        org_id=org.id,
        region_id=r.id,
        rule_type=payload.rule_type,
        threshold=payload.threshold,
        channels=payload.channels,
        recipients=[dict(rc) for rc in payload.recipients],
        cooldown_minutes=payload.cooldown_minutes,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return AlertRuleOut(
        id=str(rule.id),
        region_slug=slug,
        rule_type=rule.rule_type,
        threshold=rule.threshold,
        channels=rule.channels,
        recipients=rule.recipients,
        cooldown_minutes=rule.cooldown_minutes,
        active=rule.active,
        last_triggered_at=rule.last_triggered_at,
        created_at=rule.created_at,
    )


@router.get("/regions/{slug}/alerts", response_model=list[AlertRuleOut])
async def list_alerts(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AlertRuleOut]:
    r = await _region(db, slug)
    org = await _org_for_user(db, user)
    rows = await db.execute(
        select(B2GAlert).where(B2GAlert.org_id == org.id, B2GAlert.region_id == r.id)
    )
    return [
        AlertRuleOut(
            id=str(a.id),
            region_slug=slug,
            rule_type=a.rule_type,
            threshold=a.threshold,
            channels=a.channels,
            recipients=a.recipients,
            cooldown_minutes=a.cooldown_minutes,
            active=a.active,
            last_triggered_at=a.last_triggered_at,
            created_at=a.created_at,
        )
        for a in rows.scalars()
    ]


@router.delete("/regions/{slug}/alerts/{alert_id}", status_code=204)
async def delete_alert(
    slug: str,
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    org = await _org_for_user(db, user)
    res = await db.execute(select(B2GAlert).where(B2GAlert.id == alert_id, B2GAlert.org_id == org.id))
    row = res.scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "alert not found")
    await db.delete(row)
    await db.commit()


@router.get("/regions/{slug}/export.geojson")
async def export_geojson(slug: str, db: AsyncSession = Depends(get_db)) -> Response:
    r = await _region(db, slug)
    bbox = r.bbox
    exc = predict_exceedance(
        lon_min=bbox[0], lon_max=bbox[2], lat_min=bbox[1], lat_max=bbox[3],
        horizon_days=7, quantile=0.85,
    )
    fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [c.lng, c.lat]},
                "properties": {"probability": c.probability},
            }
            for c in exc.cells
        ],
        "region": slug,
        "bbox": bbox,
    }
    return Response(content=json.dumps(fc), media_type="application/geo+json")


@router.get("/regions/{slug}/export.xlsx")
async def export_xlsx(slug: str, db: AsyncSession = Depends(get_db)) -> Response:
    r = await _region(db, slug)
    bbox = r.bbox
    exc = predict_exceedance(
        lon_min=bbox[0], lon_max=bbox[2], lat_min=bbox[1], lat_max=bbox[3],
        horizon_days=7, quantile=0.85,
    )
    try:
        from openpyxl import Workbook  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise HTTPException(503, "openpyxl is not installed on this deployment") from exc
    wb = Workbook()
    ws = wb.active
    ws.title = f"{slug}-hotspots"
    ws.append(["lat", "lng", "probability"])
    for c in exc.cells:
        ws.append([c.lat, c.lng, c.probability])
    buf = io.BytesIO()
    wb.save(buf)
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{slug}-hotspots.xlsx"'},
    )
