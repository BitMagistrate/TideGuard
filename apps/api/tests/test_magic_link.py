"""Tests for the magic-link passwordless flow."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_magic_link_round_trip(client):
    # Request a magic link.
    r = await client.post("/auth/magic_link", json={"email": "magic-alice@example.org"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["sent"] is True
    assert "debug_token" in body  # exposed in dev/test envs only

    # Exchange the debug token for a JWT.
    r2 = await client.post("/auth/verify", json={"token": body["debug_token"]})
    assert r2.status_code == 200, r2.text
    assert r2.json()["access_token"]

    # Confirm the JWT works on /me.
    me = await client.get("/me", headers={"Authorization": f"Bearer {r2.json()['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "magic-alice@example.org"


@pytest.mark.asyncio
async def test_magic_verify_invalid_token(client):
    r = await client.post("/auth/verify", json={"token": "not-a-jwt"})
    assert r.status_code == 401
