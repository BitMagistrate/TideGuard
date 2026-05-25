"""Lesson and lesson_progress ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime, Float
from sqlalchemy.types import Uuid as PGUUID

from tideguard_api.db import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    quiz_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lang: Mapped[str] = mapped_column(Text, nullable=False, server_default="en")
    grade_band: Mapped[str | None] = mapped_column(Text, nullable=True)
    sdgs: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    practical_task_md: Mapped[str | None] = mapped_column(Text, nullable=True)


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(), ForeignKey("users.id"), primary_key=True)
    lesson_id: Mapped[uuid.UUID] = mapped_column(PGUUID(), ForeignKey("lessons.id"), primary_key=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    score: Mapped[float | None] = mapped_column(Float)
