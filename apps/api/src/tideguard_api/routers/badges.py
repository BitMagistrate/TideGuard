"""Badges router — list of available badges + per-user awarded badges."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.db import get_db
from tideguard_api.deps import get_current_user
from tideguard_api.models.badge import Badge, UserBadge
from tideguard_api.models.user import User
from tideguard_api.services.badges import BADGE_DEFS, _ensure_badges, maybe_award_badges

router = APIRouter(prefix="/badges", tags=["badges"])


@router.get("")
async def list_badges(db: AsyncSession = Depends(get_db)) -> list[dict]:
    await _ensure_badges(db)
    rows = (await db.execute(select(Badge))).scalars().all()
    by_slug = {b.slug: b for b in rows}
    return [
        {
            "slug": d.slug,
            "title": d.title,
            "description": d.description,
            "id": str(by_slug[d.slug].id) if d.slug in by_slug else None,
        }
        for d in BADGE_DEFS
    ]


@router.get("/mine")
async def my_badges(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict]:
    # Award any pending badges based on current state before returning.
    await maybe_award_badges(db, user)
    stmt = (
        select(Badge, UserBadge.awarded_at)
        .join(UserBadge, UserBadge.badge_id == Badge.id)
        .where(UserBadge.user_id == user.id)
    )
    rows = (await db.execute(stmt)).all()
    return [
        {
            "slug": b.slug,
            "title": b.title,
            "criteria": b.criteria_json,
            "awarded_at": awarded_at.isoformat() if awarded_at else None,
        }
        for b, awarded_at in rows
    ]
