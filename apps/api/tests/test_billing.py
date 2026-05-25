"""Tests for the billing endpoints + webhook idempotency."""

from __future__ import annotations

import json
import os
import uuid

import pytest

# Force the manual gateway for tests.
os.environ.setdefault("BILLING_PROVIDER", "manual")


async def _auth(client, email="biller@example.org") -> dict[str, str]:
    r = await client.post("/auth/dev_token", json={"email": email, "name": "Biller"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.asyncio
async def test_checkout_returns_url(client):
    h = await _auth(client, email="checkout@example.org")

    # Seed a "pro" tier directly via the ORM so the checkout call resolves.
    from tideguard_api.db import SessionLocal
    from tideguard_api.models.tier import Tier
    async with SessionLocal() as db:
        from sqlalchemy import select
        res = await db.execute(select(Tier).where(Tier.slug == "pro"))
        if res.scalar_one_or_none() is None:
            db.add(Tier(id=uuid.uuid4(), slug="pro", display_name="Pro", price_monthly_usd=49.0,
                        price_yearly_usd=490.0, features={}))
            await db.commit()

    r = await client.post(
        "/billing/checkout",
        json={"tier_slug": "pro", "billing_period": "monthly",
              "success_url": "https://app.tideguard.app/success",
              "cancel_url": "https://app.tideguard.app/cancel"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    assert "session_id=" in r.json()["url"]


@pytest.mark.asyncio
async def test_webhook_idempotent(client, monkeypatch):
    from tideguard_api.services.billing_gateway import ManualGateway

    # Replace settings provider with manual.
    monkeypatch.setenv("BILLING_PROVIDER", "manual")

    gateway = ManualGateway()
    payload = {
        "id": "evt_test_unique_1",
        "type": "customer.subscription.created",
        "data": {"customer": "fake", "id": "sub_fake", "metadata": {"tier_slug": "pro"}},
    }
    raw = json.dumps(payload).encode()
    sig = gateway.sign_payload(raw)

    r1 = await client.post(
        "/billing/webhook/manual",
        content=raw,
        headers={"Content-Type": "application/json", "X-Signature": sig},
    )
    assert r1.status_code == 200, r1.text
    assert r1.json()["received"] is True

    # Replay same event → still 200 but no duplicate row.
    r2 = await client.post(
        "/billing/webhook/manual",
        content=raw,
        headers={"Content-Type": "application/json", "X-Signature": sig},
    )
    assert r2.status_code == 200
    assert r2.json()["event_id"] == "evt_test_unique_1"


@pytest.mark.asyncio
async def test_webhook_invalid_signature(client):
    payload = b'{"id":"evt_bad","type":"x","data":{}}'
    r = await client.post(
        "/billing/webhook/manual", content=payload,
        headers={"Content-Type": "application/json", "X-Signature": "0" * 64},
    )
    assert r.status_code == 401
