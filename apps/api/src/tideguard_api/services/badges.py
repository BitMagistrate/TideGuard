"""Badge award service.

Defines a small set of rule-based badges and idempotently awards them to a
user. Designed to be called at the end of report / cleanup / lesson actions.

Rules
-----
- ``first-report``        — user has at least 1 report submitted (any status).
- ``cleaner-5kg``         — user has at least 5 kg collected (sum over cleanups).
- ``cleaner-50kg``        — user has at least 50 kg collected.
- ``educator-5lessons``   — user has completed at least 5 distinct lessons.
- ``leader-100xp``        — user has reached 100 XP.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tideguard_api.models.badge import Badge, UserBadge
from tideguard_api.models.cleanup import Cleanup
from tideguard_api.models.lesson import LessonProgress
from tideguard_api.models.report import Report
from tideguard_api.models.user import User


@dataclass(frozen=True)
class BadgeDef:
    slug: str
    title: str
    description: str


BADGE_DEFS: tuple[BadgeDef, ...] = (
    BadgeDef("first-report", "First Report", "Submitted your first citizen report."),
    BadgeDef("cleaner-5kg", "Cleaner — 5 kg", "Collected at least 5 kg of debris."),
    BadgeDef("cleaner-50kg", "Cleaner — 50 kg", "Collected at least 50 kg of debris."),
    BadgeDef(
        "educator-5lessons",
        "Educator — 5 lessons",
        "Completed at least 5 EE lessons.",
    ),
    BadgeDef("leader-100xp", "Leader — 100 XP", "Reached 100 XP."),
)


async def _ensure_badges(db: AsyncSession) -> dict[str, Badge]:
    """Make sure the BADGE_DEFS rows exist; return a slug->row map."""
    existing = (await db.execute(select(Badge))).scalars().all()
    by_slug: dict[str, Badge] = {b.slug: b for b in existing}
    created = False
    for d in BADGE_DEFS:
        if d.slug not in by_slug:
            row = Badge(
                id=uuid.uuid4(),
                slug=d.slug,
                title=d.title,
                criteria_json={"description": d.description},
            )
            db.add(row)
            by_slug[d.slug] = row
            created = True
    if created:
        await db.commit()
    return by_slug


async def _award_one(db: AsyncSession, user: User, badge: Badge) -> bool:
    existing = await db.execute(select(UserBadge).where(UserBadge.user_id == user.id, UserBadge.badge_id == badge.id))
    if existing.scalar_one_or_none() is not None:
        return False
    db.add(UserBadge(user_id=user.id, badge_id=badge.id))
    return True


async def maybe_award_badges(db: AsyncSession, user: User) -> list[str]:
    """Inspect the user's stats and award any qualifying badges. Idempotent.

    Returns the list of badge slugs newly awarded.
    """
    badges = await _ensure_badges(db)
    awarded: list[str] = []

    n_reports = (await db.execute(select(func.count(Report.id)).where(Report.user_id == user.id))).scalar() or 0
    if n_reports >= 1 and await _award_one(db, user, badges["first-report"]):
        awarded.append("first-report")

    kg = (
        await db.execute(select(func.coalesce(func.sum(Cleanup.kg_collected), 0.0)).where(Cleanup.user_id == user.id))
    ).scalar() or 0.0
    if kg >= 5 and await _award_one(db, user, badges["cleaner-5kg"]):
        awarded.append("cleaner-5kg")
    if kg >= 50 and await _award_one(db, user, badges["cleaner-50kg"]):
        awarded.append("cleaner-50kg")

    n_lessons = (
        await db.execute(
            select(func.count(distinct(LessonProgress.lesson_id))).where(LessonProgress.user_id == user.id)
        )
    ).scalar() or 0
    if n_lessons >= 5 and await _award_one(db, user, badges["educator-5lessons"]):
        awarded.append("educator-5lessons")

    if (user.xp or 0) >= 100 and await _award_one(db, user, badges["leader-100xp"]):
        awarded.append("leader-100xp")

    if awarded:
        await db.commit()
    return awarded
