"""Smoke + correctness tests for the v0.4 feature surface."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_forecast_explain(client):
    r = await client.get("/forecast/explain", params={"lat": 44.5, "lng": 37.8, "horizon": 7})
    assert r.status_code == 200
    body = r.json()
    assert "decomposition" in body
    assert "physics_params" in body
    assert 0.0 <= body["prediction"] <= 1.0
    assert body["ci_95"][0] <= body["prediction"] <= body["ci_95"][1] + 1e-9
    components = body["decomposition"]
    assert {
        "advection_u_ocean",
        "advection_v_ocean",
        "windage_u_wind",
        "windage_v_wind",
        "diffusion",
        "beaching",
        "biofouling",
        "stokes_drift",
    }.issubset(components.keys())


@pytest.mark.asyncio
async def test_forecast_backward(client):
    r = await client.get("/forecast/backward", params={"lat": 44.0, "lng": 37.5, "days_back": 14})
    assert r.status_code == 200
    body = r.json()
    assert body["days_back"] == 14
    assert body["target"] == [44.0, 37.5]
    assert len(body["cells"]) > 0
    total_prob = sum(c["probability"] for c in body["cells"])
    assert abs(total_prob - 1.0) < 0.05
    assert len(body["top_sources"]) >= 3


@pytest.mark.asyncio
async def test_forecast_counterfactual_disable_wind(client):
    r = await client.get(
        "/forecast/counterfactual",
        params={"bbox": "27,40,42,47", "horizon": 7, "modify": "disable_windage"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["modifications"] == {"windage": 0.0}
    # disabling wind should reduce the average concentration
    assert body["delta_mean"] <= 0.0


@pytest.mark.asyncio
async def test_forecast_active_learning(client):
    r = await client.get("/forecast/active_learning", params={"bbox": "27,40,42,47", "horizon": 7, "k": 5})
    assert r.status_code == 200
    body = r.json()
    assert len(body["top_points"]) == 5
    # ranked descending by bald_score
    scores = [p["bald_score"] for p in body["top_points"]]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_forecast_as_of_date(client):
    r = await client.get(
        "/forecast",
        params={"bbox": "27,40,42,47", "horizon": 3, "as_of_date": "2025-01-15"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["as_of_date"] == "2025-01-15"
    assert body["ground_truth_available"] is False


@pytest.mark.asyncio
async def test_forecast_as_of_date_future_rejected(client):
    r = await client.get(
        "/forecast", params={"bbox": "27,40,42,47", "horizon": 3, "as_of_date": "2099-01-01"}
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_cleanup_planner_offline(client):
    r = await client.get(
        "/cleanup_planner",
        params={"bbox": "37.4,44.0,38.0,44.6", "team_size": 10, "horizon": 5},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["team_size"] == 10
    assert len(body["recommendations"]) == 5
    for rec in body["recommendations"]:
        assert 0.0 <= rec["score"] <= 1.0
        assert "logistics" in rec
        assert "weather" in rec


@pytest.mark.asyncio
async def test_sustainability_footprint(client):
    r = await client.get("/sustainability/footprint", params={"period_days": 30, "plastic_prevented_kg": 50})
    assert r.status_code == 200
    body = r.json()
    assert body["period_days"] == 30
    assert body["plastic_prevented_kg"] == 50.0
    assert body["total_kg_co2e"] > 0


@pytest.mark.asyncio
async def test_ogc_wms_capabilities(client):
    r = await client.get("/ogc/wms", params={"service": "WMS", "request": "GetCapabilities"})
    assert r.status_code == 200
    assert "WMS_Capabilities" in r.text


@pytest.mark.asyncio
async def test_ogc_wms_getmap(client):
    r = await client.get(
        "/ogc/wms",
        params={
            "service": "WMS",
            "request": "GetMap",
            "layers": "tideguard:concentration_d7",
            "bbox": "27,40,42,47",
            "width": 128,
            "height": 128,
            "format": "image/png",
            "crs": "EPSG:4326",
        },
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.asyncio
async def test_stac_catalog(client):
    r = await client.get("/ogc/stac/catalog.json")
    assert r.status_code == 200
    body = r.json()
    assert body["type"] == "Catalog"
    assert body["id"] == "tideguard-ai"


@pytest.mark.asyncio
async def test_ogc_geojson_export(client):
    r = await client.get("/ogc/geojson", params={"bbox": "27,40,42,47", "horizon": 7})
    assert r.status_code == 200
    body = r.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) > 0
    feat = body["features"][0]
    assert feat["geometry"]["type"] == "Point"
    assert "concentration" in feat["properties"]


@pytest.mark.asyncio
async def test_developer_portal(client):
    r = await client.get("/developers")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "public-beta"
    assert len(body["endpoints"]) >= 8
