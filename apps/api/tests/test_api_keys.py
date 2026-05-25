"""Tests for the API-key CRUD endpoints (§2.2)."""

from __future__ import annotations

import uuid as _uuid

import pytest


async def _auth(client, email: str | None = None) -> dict[str, str]:
    email = email or f"billing-{_uuid.uuid4().hex[:6]}@example.org"
    r = await client.post("/auth/dev_token", json={"email": email, "name": "Billing User"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.asyncio
async def test_create_api_key_shows_plaintext_once(client):
    h = await _auth(client)
    r = await client.post("/api_keys", json={"name": "primary"}, headers=h)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["plaintext"].startswith("tg_live_")
    assert "warning" in body
    assert body["last4"] == body["plaintext"][-4:]

    # Listing should NOT return the plaintext
    r2 = await client.get("/api_keys", headers=h)
    assert r2.status_code == 200
    keys = r2.json()
    assert len(keys) >= 1
    assert "plaintext" not in keys[0]


@pytest.mark.asyncio
async def test_api_key_rotate_returns_new_secret(client):
    h = await _auth(client)
    r = await client.post("/api_keys", json={"name": "for-rotation"}, headers=h)
    assert r.status_code == 201
    key_id = r.json()["id"]
    old_plaintext = r.json()["plaintext"]

    r2 = await client.post(f"/api_keys/{key_id}/rotate", headers=h)
    assert r2.status_code == 200, r2.text
    assert r2.json()["plaintext"] != old_plaintext
    assert r2.json()["plaintext"].startswith("tg_live_")


@pytest.mark.asyncio
async def test_revoke_api_key(client):
    h = await _auth(client)
    r = await client.post("/api_keys", json={"name": "to-revoke"}, headers=h)
    assert r.status_code == 201
    key_id = r.json()["id"]

    r2 = await client.delete(f"/api_keys/{key_id}", headers=h)
    assert r2.status_code == 204

    # Revoked keys are hidden from the list.
    r3 = await client.get("/api_keys", headers=h)
    ids = [k["id"] for k in r3.json()]
    assert key_id not in ids


@pytest.mark.asyncio
async def test_api_key_listing_returns_only_own_org(client):
    h_alice = await _auth(client)
    h_bob = await _auth(client)
    # alice → already created some keys
    a_create = await client.post("/api_keys", json={"name": "alice"}, headers=h_alice)
    assert a_create.status_code == 201
    # bob should not see alice's keys
    bob_list = await client.get("/api_keys", headers=h_bob)
    ids = [k["id"] for k in bob_list.json()]
    assert a_create.json()["id"] not in ids
