"""Tests for the education endpoints (seed, list, progress)."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_seed_and_list_lessons(client):
    r = await client.post("/education/_seed")
    assert r.status_code == 200, r.text

    r2 = await client.get("/education/lessons")
    assert r2.status_code == 200
    lessons = r2.json()
    assert len(lessons) >= 10
    by_lang = {row["lang"] for row in lessons}
    # English is always present after seeding from content/lessons/
    assert "en" in by_lang


@pytest.mark.asyncio
async def test_filter_lessons_by_lang(client):
    await client.post("/education/_seed")
    r = await client.get("/education/lessons?lang=zh-TW")
    assert r.status_code == 200
    rows = r.json()
    if rows:
        # If zh-TW lessons were seeded, every row must be zh-TW
        for row in rows:
            assert row["lang"] == "zh-TW"


@pytest.mark.asyncio
async def test_progress_awards_xp(client):
    await client.post("/education/_seed")
    r = await client.post(
        "/education/progress",
        json={"lesson_slug": "marine-plastic", "score": 1.0},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["xp_awarded"] > 0
    assert body["xp_total"] >= body["xp_awarded"]
