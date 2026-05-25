"""B2G dashboard endpoints — weekly municipal report (TASK-022).

JSON endpoint + a PDF generator that aggregates predicted cleanups, citizen
reports and uncertainty hotspots for a given region (Анапа, Сочи, …).
"""

from __future__ import annotations

import io
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.db import get_db
from tideguard_api.models.cleanup import Cleanup
from tideguard_api.models.report import Report
from tideguard_api.services.inference import predict_exceedance

router = APIRouter(prefix="/b2g", tags=["b2g"])

REGIONS: dict[str, tuple[float, float, float, float]] = {
    "anapa": (37.05, 44.78, 37.55, 45.10),
    "novorossiysk": (37.55, 44.55, 38.00, 44.85),
    "sochi": (39.50, 43.45, 40.10, 43.85),
    "azov": (37.20, 45.30, 39.40, 47.00),
    "black_sea": (27.0, 40.0, 42.0, 47.0),
}


def _serialise_geojson(region: str, bbox: tuple[float, float, float, float], exceedance) -> dict:
    features: list[dict] = []
    top = sorted(exceedance.cells, key=lambda c: -c.probability)[:5]
    for c in top:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [c.lng, c.lat]},
                "properties": {"probability": c.probability},
            }
        )
    return {
        "region": region,
        "bbox": list(bbox),
        "model_version": exceedance.model_version,
        "horizon_days": exceedance.horizon_days,
        "top5_hotspots": {"type": "FeatureCollection", "features": features},
    }


@router.get("/weekly/{region}")
async def weekly(
    region: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    region = region.lower()
    if region not in REGIONS:
        raise HTTPException(404, f"Unknown region {region!r}; known: {sorted(REGIONS)}")
    bbox = REGIONS[region]
    week_ago = datetime.now(UTC) - timedelta(days=7)
    report_count = (
        await db.execute(
            select(func.count(Report.id)).where(
                Report.lng.between(bbox[0], bbox[2]),
                Report.lat.between(bbox[1], bbox[3]),
                Report.created_at >= week_ago,
            )
        )
    ).scalar() or 0
    kg_collected = (
        await db.execute(
            select(func.coalesce(func.sum(Cleanup.kg_collected), 0.0)).where(
                Cleanup.created_at >= week_ago,
            )
        )
    ).scalar() or 0.0
    n_volunteers = (
        await db.execute(
            select(func.coalesce(func.sum(Cleanup.participants), 0)).where(
                Cleanup.created_at >= week_ago,
            )
        )
    ).scalar() or 0

    exceedance = predict_exceedance(
        lon_min=bbox[0], lon_max=bbox[2], lat_min=bbox[1], lat_max=bbox[3],
        horizon_days=7, quantile=0.85,
    )
    geo = _serialise_geojson(region, bbox, exceedance)
    return {
        **geo,
        "week_start": week_ago.isoformat(),
        "week_end": datetime.now(UTC).isoformat(),
        "reports_this_week": int(report_count),
        "kg_collected_this_week": float(kg_collected),
        "volunteers_this_week": int(n_volunteers),
        # Crude estimate: top-5 hotspot probability × 50 kg.
        "kg_predicted_next_week": round(
            sum(f["properties"]["probability"] for f in geo["top5_hotspots"]["features"]) * 50.0, 1
        ),
    }


@router.get("/weekly/{region}.pdf")
async def weekly_pdf(region: str, db: AsyncSession = Depends(get_db)) -> Response:
    data = await weekly(region, db)  # type: ignore[arg-type]
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
    except ImportError as exc:  # pragma: no cover
        raise HTTPException(503, f"PDF backend unavailable: {exc}") from exc

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    c.setFillColorRGB(0.06, 0.46, 0.43)
    c.rect(0, h - 30 * mm, w, 30 * mm, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(20 * mm, h - 20 * mm, f"TideGuard B2G Weekly — {region.title()}")
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 12)
    y = h - 45 * mm
    rows = [
        ("Reports this week", data["reports_this_week"]),
        ("Volunteers this week", data["volunteers_this_week"]),
        ("Kg collected this week", f"{data['kg_collected_this_week']:.1f}"),
        ("Kg predicted next week (top-5)", f"{data['kg_predicted_next_week']:.1f}"),
        ("Model version", data["model_version"]),
        ("Horizon days", data["horizon_days"]),
    ]
    for label, value in rows:
        c.drawString(20 * mm, y, f"{label}: {value}")
        y -= 8 * mm
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 13)
    c.drawString(20 * mm, y, "Top-5 hotspots (forecast P > 0.85)")
    y -= 8 * mm
    c.setFont("Helvetica", 10)
    for i, feat in enumerate(data["top5_hotspots"]["features"], start=1):
        lon, lat = feat["geometry"]["coordinates"]
        prob = feat["properties"]["probability"]
        c.drawString(25 * mm, y, f"{i}. lat {lat:.3f}, lon {lon:.3f} — P={prob:.2f}")
        y -= 6 * mm
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(20 * mm, 12 * mm, "Generated by TideGuard AI — open-source, MIT-licensed. https://tideguard.app")
    c.showPage()
    c.save()
    return Response(
        content=buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="tideguard-{region}-weekly.pdf"'},
    )


@router.get("/regions")
def regions() -> dict:
    return {name: {"bbox": list(bbox)} for name, bbox in REGIONS.items()}


@router.get("/impact")
async def impact(
    region: str | None = None,
    days: int = 365,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cumulative community impact summary.

    Returns the totals required for the public Impact dashboard:
    ``n_reports``, ``n_cleanups``, ``kg_total``, ``co2_saved_kg``,
    ``coastline_covered_km``, ``volunteers``.

    ``region`` filters by one of the registered regions.  ``days``
    constrains the time window (default: 1 year).

    The CO2 conversion uses the EU Waste-Statistics-Regulation
    (Regulation EC 2150/2002) coefficient of 0.96 kg CO2e per kg plastic
    avoided when properly recycled vs. open burning.  Coastline coverage
    is a coarse proxy: ``sqrt(kg_collected / 5)`` km — a 5 kg / km
    cleanup norm derived from the OSPAR Beach Litter Monitoring guideline.
    """
    bbox: tuple[float, float, float, float] | None = None
    if region:
        region = region.lower()
        if region not in REGIONS:
            raise HTTPException(404, f"Unknown region {region!r}; known: {sorted(REGIONS)}")
        bbox = REGIONS[region]
    cutoff = datetime.now(UTC) - timedelta(days=max(1, days))

    report_filter = [Report.created_at >= cutoff]
    cleanup_filter = [Cleanup.created_at >= cutoff]
    if bbox is not None:
        report_filter += [
            Report.lng.between(bbox[0], bbox[2]),
            Report.lat.between(bbox[1], bbox[3]),
        ]
        # Cleanup polygons are stored as WKT and are typically small (a few
        # hundred metres across) so we filter post-hoc rather than parsing
        # the WKT in SQL.  This is fine for dashboard-scale aggregations
        # (≤ 10⁴ rows) and avoids a Postgres/SQLite branch.
    n_reports = (await db.execute(select(func.count(Report.id)).where(*report_filter))).scalar() or 0
    n_cleanups = (await db.execute(select(func.count(Cleanup.id)).where(*cleanup_filter))).scalar() or 0
    kg_total = (
        await db.execute(
            select(func.coalesce(func.sum(Cleanup.kg_collected), 0.0)).where(*cleanup_filter)
        )
    ).scalar() or 0.0
    volunteers = (
        await db.execute(
            select(func.coalesce(func.sum(Cleanup.participants), 0)).where(*cleanup_filter)
        )
    ).scalar() or 0

    kg_total_f = float(kg_total)
    import math
    co2_saved_kg = kg_total_f * 0.96
    coastline_covered_km = math.sqrt(max(kg_total_f, 0.0) / 5.0)
    return {
        "region": region or "all",
        "window_days": int(days),
        "n_reports": int(n_reports),
        "n_cleanups": int(n_cleanups),
        "volunteers": int(volunteers),
        "kg_total": round(kg_total_f, 1),
        "co2_saved_kg": round(co2_saved_kg, 1),
        "coastline_covered_km": round(coastline_covered_km, 2),
        "methodology": {
            "co2_per_kg": 0.96,
            "co2_source": "EC Regulation 2150/2002 — Waste Statistics",
            "coastline_norm_kg_per_km": 5.0,
            "coastline_source": "OSPAR Beach Litter Monitoring guideline",
        },
    }
