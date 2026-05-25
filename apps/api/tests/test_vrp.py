"""Tests for the VRP solver (§4.2.4)."""

from __future__ import annotations

from tideguard_api.services.vrp_solver import Hotspot, solve_vrp


def test_empty_hotspots_returns_empty_routes():
    result = solve_vrp(depot=(44.0, 39.0), hotspots=[])
    assert result.routes == []
    assert result.solver_status == "EMPTY"


def test_solver_assigns_hotspots():
    hotspots = [
        Hotspot(lat=44.0 + i * 0.01, lng=39.0 + i * 0.01, probability=0.5 + i * 0.05,
                est_kg=30.0, hotspot_id=f"hp-{i}")
        for i in range(8)
    ]
    result = solve_vrp(depot=(44.0, 39.0), hotspots=hotspots, team_size=2, capacity_kg=150.0)
    assert len(result.routes) >= 1
    visited = sum(len(r.stops) for r in result.routes)
    assert visited + len(result.unassigned_hotspots) >= len(hotspots) - 1


def test_capacity_respected():
    hotspots = [Hotspot(lat=44.0, lng=39.0 + i * 0.01, probability=0.8, est_kg=80.0, hotspot_id=f"hp-{i}")
                 for i in range(4)]
    result = solve_vrp(depot=(44.0, 39.0), hotspots=hotspots, team_size=1, capacity_kg=100.0)
    for r in result.routes:
        assert r.total_kg_est <= 100.0
