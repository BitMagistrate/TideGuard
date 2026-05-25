"""Gamification badges ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime
from sqlalchemy.types import Uuid as PGUUID

from tideguard_api.db import Base


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    criteria_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class UserBadge(Base):
    __tablename__ = "user_badges"

    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(), ForeignKey("users.id"), primary_key=True)
    badge_id: Mapped[uuid.UUID] = mapped_column(PGUUID(), ForeignKey("badges.id"), primary_key=True)
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
