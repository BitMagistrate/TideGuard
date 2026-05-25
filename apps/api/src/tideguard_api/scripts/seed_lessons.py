"""Seed EE lessons from ``content/lessons/*.md`` into the DB.

Called from the lifespan startup when ``AUTO_SEED_ON_STARTUP=1``. Idempotent:
existing lesson slugs are left untouched. Pairs with the
``/education/_seed`` admin endpoint (same parsing logic).
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from pathlib import Path

from sqlalchemy import select

from tideguard_api.db import SessionLocal
from tideguard_api.models.lesson import Lesson

log = logging.getLogger(__name__)

# Candidate locations for the lessons content directory. The Docker image and
# the local monorepo layouts are both supported so the seeder works the same
# way in CI, on a developer machine and on Hugging Face Spaces.
_CONTENT_CANDIDATES: tuple[Path, ...] = (
    Path(__file__).resolve().parents[5] / "content" / "lessons",
    Path("/home/user/app/content/lessons"),
    Path.cwd() / "content" / "lessons",
)


def _find_content_dir() -> Path | None:
    for p in _CONTENT_CANDIDATES:
        if p.exists() and p.is_dir():
            return p
    return None


def _parse_lesson(md_path: Path) -> dict | None:
    text = md_path.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not fm_match:
        return None
    fm, body = fm_match.groups()
    meta: dict[str, str] = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            meta[key.strip()] = val.strip().strip('"')
    slug = meta.get("slug")
    if not slug:
        return None

    quiz_match = re.search(r"```json\n(\[.*?\])\n```", body, re.S)
    quiz = json.loads(quiz_match.group(1)) if quiz_match else []
    content_md = body
    if quiz_match:
        content_md = body[: quiz_match.start()].rstrip()

    sdgs_field = meta.get("sdgs", "")
    sdgs_list = [int(x) for x in re.findall(r"\d+", sdgs_field)]

    task_match = re.search(r"```task\n(.*?)\n```", body, re.S)
    practical_task = task_match.group(1).strip() if task_match else None
    if task_match:
        content_md = content_md.replace(task_match.group(0), "").rstrip()

    return {
        "slug": slug,
        "title": meta.get("title", slug),
        "content_md": content_md,
        "quiz": {"questions": quiz},
        "xp_reward": int(meta.get("xp", 50)),
        "order_index": int(meta.get("order", 0)),
        "lang": meta.get("lang", "en"),
        "grade_band": meta.get("grade") or meta.get("grade_band"),
        "sdgs": {"goals": sdgs_list},
        "practical_task_md": practical_task,
    }


async def main() -> int:
    """Insert every parseable lesson into the DB. Returns rows inserted."""
    content_dir = _find_content_dir()
    if content_dir is None:
        log.warning("seed_lessons: content/lessons not found")
        return 0
    md_files = list(content_dir.glob("*.md"))
    md_files += list(content_dir.glob("*/*.md"))

    inserted = 0
    async with SessionLocal() as db:
        for md_path in sorted(md_files):
            parsed = _parse_lesson(md_path)
            if not parsed:
                continue
            existing = await db.execute(
                select(Lesson).where(Lesson.slug == parsed["slug"])
            )
            if existing.scalar_one_or_none():
                continue
            db.add(
                Lesson(
                    id=uuid.uuid4(),
                    slug=parsed["slug"],
                    title=parsed["title"],
                    content_md=parsed["content_md"],
                    quiz_json=parsed["quiz"],
                    xp_reward=parsed["xp_reward"],
                    order_index=parsed["order_index"],
                    lang=parsed["lang"],
                    grade_band=parsed["grade_band"],
                    sdgs=parsed["sdgs"],
                    practical_task_md=parsed["practical_task_md"],
                )
            )
            inserted += 1
        await db.commit()
    log.info("seed_lessons: inserted %d lesson rows", inserted)
    return inserted
