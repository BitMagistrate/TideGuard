"""Tests for the Adopt-a-Beach endpoints (§6)."""

from __future__ import annotations

import uuid

import pytest


async def _seed_segment(slug="anapa-001-test") -> str:
    from tideguard_api.db import SessionLocal
    from tideguard_api.models.beach_segment import BeachSegment

    async with SessionLocal() as db:
        seg = BeachSegment(
            id=uuid.uuid4(),
            slug=slug,
            geom_wkt="LINESTRING (37.3 44.85, 37.31 44.85)",
            length_m=1000.0,
            midpoint_lat=44.85,
            midpoint_lng=37.305,
            display_name="Test segment Anapa-001",
            status="available",
        )
        db.add(seg)
        await db.commit()
        await db.refresh(seg)
        return str(seg.id)


async def _auth(client, email="adopter@example.org") -> dict[str, str]:
    r = await client.post("/auth/dev_token", json={"email": email, "name": "Adopter"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.asyncio
async def test_list_and_get_segment(client):
    seg_id = await _seed_segment(slug=f"anapa-test-{uuid.uuid4().hex[:6]}")
    r = await client.get("/adopt/segments?status=available")
    assert r.status_code == 200
    found = [s for s in r.json() if s["id"] == seg_id]
    assert found, "newly-seeded segment should appear in the list"

    slug = found[0]["slug"]
    r2 = await client.get(f"/adopt/segments/{slug}")
    assert r2.status_code == 200
    assert r2.json()["status"] in ("available", "reserved")


@pytest.mark.asyncio
async def test_bbox_filter(client):
    await _seed_segment(slug=f"anapa-test-{uuid.uuid4().hex[:6]}")
    r = await client.get("/adopt/segments?bbox=36.0,44.0,38.0,45.0")
    assert r.status_code == 200
    assert all(36 <= s["midpoint_lng"] <= 38 for s in r.json())


@pytest.mark.asyncio
async def test_checkout_creates_adoption(client):
    h = await _auth(client, email=f"adopter-{uuid.uuid4().hex[:5]}@example.org")
    seg_id = await _seed_segment(slug=f"anapa-ck-{uuid.uuid4().hex[:6]}")
    r = await client.post(
        "/adopt/checkout",
        json={"segment_id": seg_id, "tier": "adopt_individual", "period": "monthly"},
        headers=h,
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "pending_payment"

    r2 = await client.get("/adopt/mine", headers=h)
    assert r2.status_code == 200
    assert len(r2.json()) >= 1


@pytest.mark.asyncio
async def test_double_adoption_blocked(client):
    h = await _auth(client, email=f"adopter-dup-{uuid.uuid4().hex[:5]}@example.org")
    seg_id = await _seed_segment(slug=f"anapa-dup-{uuid.uuid4().hex[:6]}")
    r1 = await client.post(
        "/adopt/checkout",
        json={"segment_id": seg_id, "tier": "adopt_individual", "period": "monthly"},
        headers=h,
    )
    assert r1.status_code == 201
    r2 = await client.post(
        "/adopt/checkout",
        json={"segment_id": seg_id, "tier": "adopt_individual", "period": "monthly"},
        headers=h,
    )
    assert r2.status_code == 409
