"""Leaderboard endpoint — top users by XP."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.db import get_db
from tideguard_api.models.user import User

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("")
async def leaderboard(
    scope: str = Query("global", pattern="^(global|school|region)$"),
    school_id: str | None = Query(None, description="UUID; required when scope=school"),
    country: str | None = Query(None, description="ISO-3166 alpha-2; required when scope=region"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    stmt = select(User).order_by(User.xp.desc()).limit(limit)

    if scope == "school":
        if not school_id:
            raise HTTPException(400, "scope=school requires school_id")
        try:
            sid = uuid.UUID(school_id)
        except ValueError as exc:
            raise HTTPException(400, "school_id must be a UUID") from exc
        stmt = stmt.where(User.school_id == sid)
    elif scope == "region":
        if not country:
            raise HTTPException(400, "scope=region requires country")
        stmt = stmt.where(User.country == country.upper())

    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "rank": i + 1,
            "user_id": str(u.id),
            "name": u.name or u.email.split("@")[0],
            "xp": u.xp,
            "school_id": str(u.school_id) if u.school_id else None,
            "country": u.country,
        }
        for i, u in enumerate(rows)
    ]
