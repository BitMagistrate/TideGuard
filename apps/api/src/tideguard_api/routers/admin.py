"""Admin endpoints — KPI dashboard data + public KPI snapshot."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.db import get_db
from tideguard_api.deps import require_admin
from tideguard_api.models.cleanup import Cleanup
from tideguard_api.models.lesson import LessonProgress
from tideguard_api.models.report import Report
from tideguard_api.models.school import School
from tideguard_api.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


async def _kpi_snapshot(db: AsyncSession) -> dict:
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_reports = (await db.execute(select(func.count(Report.id)))).scalar() or 0
    approved_reports = (
        await db.execute(select(func.count(Report.id)).where(Report.status == "approved"))
    ).scalar() or 0
    total_cleanups = (await db.execute(select(func.count(Cleanup.id)))).scalar() or 0
    total_kg = (await db.execute(select(func.coalesce(func.sum(Cleanup.kg_collected), 0.0)))).scalar() or 0.0
    total_schools = (await db.execute(select(func.count(School.id)))).scalar() or 0
    lessons_completed = (await db.execute(select(func.count(LessonProgress.user_id)))).scalar() or 0
    lessons_completed_distinct = (await db.execute(select(func.count(distinct(LessonProgress.user_id))))).scalar() or 0
    return {
        "users": int(total_users),
        "reports_total": int(total_reports),
        "reports_approved": int(approved_reports),
        "cleanups": int(total_cleanups),
        "kg_collected": float(total_kg),
        "schools": int(total_schools),
        "lessons_completed": int(lessons_completed),
        "lessons_completed_distinct": int(lessons_completed_distinct),
    }


@router.get("/kpi")
async def kpi(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    """Authenticated impact + engagement KPI dashboard."""
    return await _kpi_snapshot(db)


@router.get("/kpi_public")
async def kpi_public(db: AsyncSession = Depends(get_db)) -> dict:
    """Public, read-only KPI snapshot rendered on the landing page.

    Returns the same shape as ``/admin/kpi`` but without any per-user data.
    Useful for the marketing site / jury landing page where we want to show
    *real* numbers without exposing the admin token.
    """
    return await _kpi_snapshot(db)


@router.post("/seed-all")
async def seed_all() -> dict:
    """Run every idempotent demo-data seeder in order.

    Convenience endpoint for fresh deployments (Fly.io, Render, etc.) so the
    operator does not have to ``ssh`` into the container to run three Python
    scripts. Each underlying script is idempotent (skips rows whose unique
    slug already exists), so calling this twice is safe.

    Returns a per-step status payload. Errors are caught so a single failing
    seeder does not abort the others.
    """
    from tideguard_api.scripts import seed_beach_segments, seed_regions, seed_tiers

    steps = [
        ("regions", seed_regions.main),
        ("beach_segments", seed_beach_segments.main),
        ("tiers", seed_tiers.main),
    ]
    results: dict[str, str] = {}
    for name, fn in steps:
        try:
            await fn()
            results[name] = "ok"
        except Exception as exc:  # noqa: BLE001
            results[name] = f"error: {exc!r}"
    return {"seeded": results}
