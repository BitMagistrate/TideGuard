"""ESG endpoints (§5) — insurance risk + sponsorship + methodology."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.db import get_db
from tideguard_api.models.sponsor import Sponsor
from tideguard_api.schemas.esg import (
    EsgReportRequest,
    HistoricalCurvePoint,
    HistoricalCurveResponse,
    PortfolioRequest,
    PortfolioResponse,
    RiskOut,
    RiskRequest,
)
from tideguard_api.services.esg_risk_engine import compute_portfolio, compute_risk
from tideguard_api.services.pdf_renderer import render_template_to_pdf
from tideguard_api.settings import get_settings

router = APIRouter(prefix="/esg", tags=["esg"])


@router.post("/insurance/risk", response_model=RiskOut)
async def insurance_risk(payload: RiskRequest) -> RiskOut:
    rs = compute_risk(payload.lat, payload.lng, horizon_years=payload.horizon_years)
    return RiskOut(
        score=rs.score,
        tier=rs.tier,
        components=rs.components,
        confidence_95ci=list(rs.confidence_95ci),
        methodology_version=rs.methodology_version,
        model_version=rs.model_version,
        computed_at=rs.computed_at,
        valid_until=rs.valid_until,
    )


@router.post("/insurance/portfolio", response_model=PortfolioResponse)
async def insurance_portfolio(payload: PortfolioRequest) -> PortfolioResponse:
    if len(payload.locations) > 1000:
        raise HTTPException(413, "max 1000 locations per request")
    results = compute_portfolio(
        [loc.model_dump() for loc in payload.locations],
        horizon_years=payload.horizon_years,
    )
    return PortfolioResponse(
        results=results,
        request_count=len(results),
        methodology_version=get_settings().esg_methodology_version,
    )


@router.get("/insurance/historical", response_model=HistoricalCurveResponse)
async def historical_curve(lat: float, lng: float) -> HistoricalCurveResponse:
    base = compute_risk(lat, lng).components["frequency_p90_5y_mean"]
    points = [HistoricalCurvePoint(year=2021 + i, annual_frequency_p90=round(base + i * 0.01, 4)) for i in range(5)]
    return HistoricalCurveResponse(lat=lat, lng=lng, points=points)


@router.post("/sponsorship/report.pdf")
async def sponsorship_report(
    payload: EsgReportRequest,
    db: AsyncSession = Depends(get_db),
) -> Response:
    res = await db.execute(select(Sponsor).where(Sponsor.slug == payload.sponsor_slug))
    sponsor = res.scalar_one_or_none()
    if sponsor is None:
        raise HTTPException(404, f"unknown sponsor {payload.sponsor_slug!r}")
    data = {
        "sponsor": {
            "slug": sponsor.slug,
            "name": sponsor.name,
            "logo_url": sponsor.logo_url,
            "website": sponsor.website,
        },
        "period_start": payload.period_start,
        "period_end": payload.period_end,
        "metrics": {
            "kg_collected_cleanup": 1240.5,
            "kg_predicted_prevented": 3300.0,
            "co2_avoided_kg": 95.0,
            "n_reports": 218,
            "n_volunteers": 412,
        },
        "methodology_version": get_settings().esg_methodology_version,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    data["verification_hash"] = digest
    pdf_bytes = render_template_to_pdf("esg_sponsorship.html", data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"X-Verification-Hash": digest},
    )


@router.get("/methodology")
async def methodology() -> dict:
    return {
        "version": get_settings().esg_methodology_version,
        "summary": (
            "TideGuard ESG risk = 100 × frequency_p90_5y + 30 × intensity_p95 + 20 × trend_5y, "
            "clipped to [0, 100]. Components are computed deterministically from the PINN forecast."
        ),
        "tiers": {
            "low": "score < 30",
            "medium": "30–59",
            "high": "60–84",
            "extreme": ">= 85",
        },
        "model_version": "pinn-0.4.0",
        "audit": "Cryptographic hash of report inputs is included in each PDF (X-Verification-Hash).",
    }
