"""Tests for the auth endpoints (dev_token + JWT-protected access)."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_dev_token_round_trip(client):
    r = await client.post("/auth/dev_token", json={"email": "alice@example.org", "name": "Alice"})
    assert r.status_code == 200, r.text
    payload = r.json()
    token = payload["access_token"]
    assert token
    assert payload["user_id"]

    r2 = await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200, r2.text
    assert r2.json()["email"] == "alice@example.org"


@pytest.mark.asyncio
async def test_invalid_token_rejected(client):
    r = await client.get("/me", headers={"Authorization": "Bearer not-a-real-jwt"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_dev_token_email_validation(client):
    r = await client.post("/auth/dev_token", json={"email": "not-an-email"})
    assert r.status_code == 422
