"""Smoke tests for the new /b2g/impact, /impact/causal and auth endpoints (v0.3)."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_b2g_impact_endpoint(client) -> None:
    response = await client.get("/b2g/impact?days=30")
    assert response.status_code == 200
    body = response.json()
    assert "n_reports" in body
    assert "n_cleanups" in body
    assert "kg_total" in body
    assert "co2_saved_kg" in body
    assert "coastline_covered_km" in body
    assert "methodology" in body


@pytest.mark.asyncio
async def test_b2g_impact_filter_by_region(client) -> None:
    response = await client.get("/b2g/impact?region=anapa&days=30")
    assert response.status_code == 200
    assert response.json()["region"] == "anapa"


@pytest.mark.asyncio
async def test_causal_impact_endpoint(client) -> None:
    qs = (
        "treated=1,2,3,4,8,9,10"
        "&donors=1,2,3,4,4,5,6;0,1,2,3,3,4,5"
        "&intervention_index=4"
    )
    response = await client.get(f"/impact/causal?{qs}")
    assert response.status_code == 200
    body = response.json()
    assert len(body["counterfactual"]) == 7
    assert body["cumulative_impact"] > 0
    assert 0.0 < body["relative_effect"] < 5.0
    assert abs(sum(body["donor_weights"]) - 1.0) < 1e-6


@pytest.mark.asyncio
async def test_jwks_endpoint(client) -> None:
    response = await client.get("/auth/jwks.json")
    assert response.status_code == 200
    body = response.json()
    assert body["keys"] and "kty" in body["keys"][0]


@pytest.mark.asyncio
async def test_oidc_discovery_endpoint(client) -> None:
    response = await client.get("/.well-known/openid-configuration")
    assert response.status_code == 200
    body = response.json()
    assert "issuer" in body
    assert "jwks_uri" in body
    assert "id_token_signing_alg_values_supported" in body


@pytest.mark.asyncio
async def test_request_id_header_is_returned(client) -> None:
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.headers.get("x-request-id"), "RequestIdMiddleware did not stamp header"


@pytest.mark.asyncio
async def test_request_id_echoed_when_provided(client) -> None:
    response = await client.get("/healthz", headers={"X-Request-Id": "abc-123"})
    assert response.headers.get("x-request-id") == "abc-123"
