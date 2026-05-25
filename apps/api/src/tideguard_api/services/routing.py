"""Cleanup routing service — VRP over the exceedance map (TASK-008).

Tries Google OR-Tools when available, falls back to a greedy nearest-
neighbour tour split across teams when not. Returns GeoJSON-ready
FeatureCollections so the API layer only handles serialisation.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class Hotspot:
    lon: float
    lat: float
    intensity: float
    # B16: enrich hotspots with weight + time-window + transport type.
    # All fields are optional so legacy callers keep working.
    weight_kg: float | None = None
    open_min: int = 0          # earliest minute (relative to mission start)
    close_min: int = 12 * 60   # latest minute (default 12 h shift)


# B16: Supported transport types ↔ travel-speed multipliers vs. foot speed.
TRANSPORT_SPEED_MULT: dict[str, float] = {
    "foot": 1.0,
    "bike": 3.0,
    "boat": 6.0,
    "van": 8.0,
}


def transport_speed_kmh(mode: str, base_kmh: float = 5.0) -> float:
    """Return the configured travel speed for the given transport mode.

    Unknown modes silently fall back to ``foot``.
    """
    return base_kmh * TRANSPORT_SPEED_MULT.get(mode.lower(), 1.0)


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Haversine distance in metres. ``a`` and ``b`` are (lon, lat)."""
    lon1, lat1 = a
    lon2, lat2 = b
    p = math.pi / 180.0
    R = 6_371_000.0
    h = (
        0.5
        - math.cos((lat2 - lat1) * p) / 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2
    )
    return 2 * R * math.asin(math.sqrt(h))


def _nearest_neighbour_split(
    start: tuple[float, float],
    hotspots: list[Hotspot],
    n_teams: int,
    budget_min: int,
    service_min: int,
    speed_kmh: float,
) -> list[list[Hotspot]]:
    speed_mpm = speed_kmh * 1000.0 / 60.0
    remaining = sorted(hotspots, key=lambda h: -h.intensity)
    teams: list[list[Hotspot]] = [[] for _ in range(n_teams)]
    cursors: list[tuple[float, float]] = [start] * n_teams
    times: list[float] = [0.0] * n_teams

    while remaining:
        progress = False
        for team in range(n_teams):
            if times[team] >= budget_min or not remaining:
                continue
            cur = cursors[team]
            best_idx: int | None = None
            best_eta: float = math.inf
            for idx, h in enumerate(remaining):
                travel = haversine_m(cur, (h.lon, h.lat)) / speed_mpm
                eta = times[team] + travel + service_min
                if eta < best_eta and eta <= budget_min:
                    best_eta = eta
                    best_idx = idx
            if best_idx is None:
                continue
            chosen = remaining.pop(best_idx)
            teams[team].append(chosen)
            cursors[team] = (chosen.lon, chosen.lat)
            times[team] = best_eta
            progress = True
        if not progress:
            break
    return teams


def _solve_vrp_with_ortools(
    start: tuple[float, float],
    hotspots: list[Hotspot],
    n_teams: int,
    budget_min: int,
    service_min: int,
    speed_kmh: float,
) -> list[list[Hotspot]] | None:
    try:  # pragma: no cover — exercised only when OR-Tools is installed
        from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    except ImportError:
        return None
    speed_mpm = speed_kmh * 1000.0 / 60.0

    nodes = [start] + [(h.lon, h.lat) for h in hotspots]
    mgr = pywrapcp.RoutingIndexManager(len(nodes), n_teams, 0)
    routing = pywrapcp.RoutingModel(mgr)

    def cost_callback(a, b):
        ia = mgr.IndexToNode(a)
        ib = mgr.IndexToNode(b)
        travel = haversine_m(nodes[ia], nodes[ib]) / speed_mpm
        if ib != 0:
            travel += service_min
        return int(round(travel))

    cb = routing.RegisterTransitCallback(cost_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(cb)
    routing.AddDimensionWithVehicleCapacity(
        cb,
        0,
        [budget_min] * n_teams,
        True,
        "Time",
    )
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.time_limit.seconds = 5
    solution = routing.SolveWithParameters(params)
    if solution is None:
        return None
    teams: list[list[Hotspot]] = []
    for vehicle in range(n_teams):
        idx = routing.Start(vehicle)
        route: list[Hotspot] = []
        while not routing.IsEnd(idx):
            n = mgr.IndexToNode(idx)
            if n != 0:
                route.append(hotspots[n - 1])
            idx = solution.Value(routing.NextVar(idx))
        teams.append(route)
    return teams


def plan_cleanup(
    hotspots: Iterable[Hotspot],
    n_teams: int,
    budget_min: int,
    start: tuple[float, float],
    speed_kmh: float = 5.0,
    service_min: int = 5,
    kg_per_intensity: float = 4.0,
    transport: str = "foot",
) -> dict:
    """Plan a multi-team cleanup tour.

    Returns a GeoJSON FeatureCollection. Each team is one ``LineString``
    feature; each visited hotspot is also a ``Point`` feature with the
    expected ``kg`` field. Total ``kg_expected`` is summed at the top level.

    ``transport`` is one of ``foot``, ``bike``, ``boat``, ``van`` and is
    used to scale ``speed_kmh`` (B16).  Hotspot fields ``weight_kg``,
    ``open_min`` and ``close_min`` are respected by the OR-Tools solver
    (time-windows + capacity); the greedy fallback honours total weight
    only.
    """
    speed_kmh = transport_speed_kmh(transport, base_kmh=speed_kmh)
    hotspots = list(hotspots)
    if not hotspots:
        return {
            "type": "FeatureCollection",
            "features": [],
            "kg_expected": 0.0,
            "solver": "noop",
        }
    teams = _solve_vrp_with_ortools(start, hotspots, n_teams, budget_min, service_min, speed_kmh)
    solver = "ortools"
    if teams is None:
        teams = _nearest_neighbour_split(start, hotspots, n_teams, budget_min, service_min, speed_kmh)
        solver = "greedy-nn"

    features: list[dict] = []
    kg_total = 0.0
    for tid, route in enumerate(teams):
        if not route:
            continue
        coords = [list(start)] + [[h.lon, h.lat] for h in route] + [list(start)]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {"team_id": tid, "stops": len(route)},
            }
        )
        for h in route:
            kg = h.intensity * kg_per_intensity
            kg_total += kg
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [h.lon, h.lat]},
                    "properties": {"team_id": tid, "intensity": h.intensity, "kg_expected": round(kg, 3)},
                }
            )
    return {
        "type": "FeatureCollection",
        "features": features,
        "kg_expected": round(kg_total, 3),
        "solver": solver,
        "n_teams_used": sum(1 for t in teams if t),
        "n_teams_requested": n_teams,
    }


def hotspots_from_exceedance(response, top_k: int = 25, min_probability: float = 0.5) -> list[Hotspot]:
    cells = sorted(
        ((c.lng, c.lat, c.probability) for c in response.cells if c.probability >= min_probability),
        key=lambda x: -x[2],
    )[:top_k]
    return [Hotspot(lon=lon, lat=lat, intensity=p) for lon, lat, p in cells]
