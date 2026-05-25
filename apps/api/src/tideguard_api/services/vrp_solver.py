"""Vehicle Routing Problem solver — OR-Tools backend with greedy fallback.

Inputs: list of hotspot coordinates (with probability + estimated kg),
team count, capacity, working window, depot. Output: routes ordered by
the optimiser.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Hotspot:
    lat: float
    lng: float
    probability: float
    est_kg: float
    hotspot_id: str = ""


@dataclass(slots=True)
class RouteStop:
    seq: int
    lat: float
    lng: float
    hotspot_id: str
    arrive: str
    depart: str
    est_kg: float
    p_exceed: float


@dataclass(slots=True)
class Route:
    team_id: int
    stops: list[RouteStop]
    total_distance_km: float
    total_time_min: int
    total_kg_est: float


@dataclass(slots=True)
class VrpResult:
    routes: list[Route]
    unassigned_hotspots: list[str]
    total_kg_est: float
    solver_status: str
    solve_time_ms: int


def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def solve_vrp(
    depot: tuple[float, float],
    hotspots: list[Hotspot],
    team_size: int = 4,
    capacity_kg: float = 200.0,
    time_window_minutes: int = 540,
    service_minutes_per_stop: int = 40,
    speed_kmh: float = 35.0,
    time_limit_ms: int = 10_000,
) -> VrpResult:
    """Solve a Capacitated VRP with Time Windows.

    The function tries OR-Tools first; on failure (e.g. infeasible or
    library missing) falls back to a greedy nearest-neighbour heuristic.
    """
    start = time.monotonic()
    if not hotspots:
        return VrpResult([], [], 0.0, "EMPTY", 0)

    try:
        return _ortools_solve(
            depot, hotspots, team_size, capacity_kg, time_window_minutes,
            service_minutes_per_stop, speed_kmh, time_limit_ms,
        )
    except Exception as exc:  # noqa: BLE001 — fall back gracefully
        logger.info("OR-Tools failed (%s); using greedy fallback", exc)
        result = _greedy_solve(
            depot, hotspots, team_size, capacity_kg, time_window_minutes,
            service_minutes_per_stop, speed_kmh,
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        result.solver_status = "GREEDY_FALLBACK"
        result.solve_time_ms = elapsed_ms
        return result


def _format_min(start_min: int, offset: int) -> str:
    minutes = start_min + offset
    h, m = divmod(int(minutes), 60)
    return f"{h:02d}:{m:02d}"


def _greedy_solve(
    depot: tuple[float, float],
    hotspots: list[Hotspot],
    team_size: int,
    capacity_kg: float,
    time_window_minutes: int,
    service_minutes_per_stop: int,
    speed_kmh: float,
) -> VrpResult:
    remaining = sorted(
        hotspots, key=lambda h: -h.probability * (h.est_kg or 1.0)
    )
    routes: list[Route] = []
    start_min = 8 * 60  # 08:00
    for team in range(team_size):
        if not remaining:
            break
        current = depot
        time_used = 0
        kg_used = 0.0
        distance_km = 0.0
        stops: list[RouteStop] = []
        seq = 0
        while remaining:
            # Nearest hotspot fitting capacity & time window
            best_i = -1
            best_d = math.inf
            for i, h in enumerate(remaining):
                d = _haversine_km(current, (h.lat, h.lng))
                if d < best_d:
                    if kg_used + h.est_kg <= capacity_kg:
                        travel_min = (d / speed_kmh) * 60.0
                        if time_used + travel_min + service_minutes_per_stop <= time_window_minutes:
                            best_d = d
                            best_i = i
            if best_i < 0:
                break
            h = remaining.pop(best_i)
            travel_min = (best_d / speed_kmh) * 60.0
            arrive_off = int(time_used + travel_min)
            depart_off = arrive_off + service_minutes_per_stop
            seq += 1
            stops.append(
                RouteStop(
                    seq=seq, lat=h.lat, lng=h.lng, hotspot_id=h.hotspot_id or f"hp-{seq}",
                    arrive=_format_min(start_min, arrive_off),
                    depart=_format_min(start_min, depart_off),
                    est_kg=h.est_kg, p_exceed=h.probability,
                )
            )
            time_used = depart_off
            distance_km += best_d
            kg_used += h.est_kg
            current = (h.lat, h.lng)
        # return to depot
        return_d = _haversine_km(current, depot)
        distance_km += return_d
        time_used += int((return_d / speed_kmh) * 60.0)
        routes.append(
            Route(
                team_id=team + 1, stops=stops,
                total_distance_km=round(distance_km, 2),
                total_time_min=int(time_used),
                total_kg_est=round(kg_used, 1),
            )
        )
    unassigned = [h.hotspot_id or f"hp-?-{i}" for i, h in enumerate(remaining)]
    total_kg = sum(r.total_kg_est for r in routes)
    return VrpResult(
        routes=routes, unassigned_hotspots=unassigned,
        total_kg_est=round(total_kg, 1),
        solver_status="GREEDY", solve_time_ms=0,
    )


def _ortools_solve(
    depot: tuple[float, float],
    hotspots: list[Hotspot],
    team_size: int,
    capacity_kg: float,
    time_window_minutes: int,
    service_minutes_per_stop: int,
    speed_kmh: float,
    time_limit_ms: int,
) -> VrpResult:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2  # type: ignore

    locations = [depot, *[(h.lat, h.lng) for h in hotspots]]
    n = len(locations)
    distance_matrix = [[int(_haversine_km(locations[i], locations[j]) * 1000) for j in range(n)] for i in range(n)]
    demands = [0] + [int(round(h.est_kg)) for h in hotspots]
    cap_int = max(int(capacity_kg), 1)

    manager = pywrapcp.RoutingIndexManager(n, team_size, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        return distance_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit_idx = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)

    def demand_callback(from_index: int) -> int:
        return demands[manager.IndexToNode(from_index)]

    demand_idx = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_idx, 0, [cap_int] * team_size, True, "Capacity"
    )

    # Time dimension: travel time + service time per visited stop.
    def time_callback(from_index: int, to_index: int) -> int:
        i = manager.IndexToNode(from_index)
        j = manager.IndexToNode(to_index)
        travel_min = int(distance_matrix[i][j] / 1000.0 / speed_kmh * 60.0)
        service = service_minutes_per_stop if i != 0 else 0
        return travel_min + service

    time_idx = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(time_idx, 0, time_window_minutes, True, "Time")

    # Penalise dropping a stop so the optimiser tries to include all hotspots.
    for node in range(1, n):
        routing.AddDisjunction([manager.NodeToIndex(node)], 1_000_000)

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_params.time_limit.seconds = max(time_limit_ms // 1000, 1)

    start = time.monotonic()
    solution = routing.SolveWithParameters(search_params)
    elapsed_ms = int((time.monotonic() - start) * 1000)

    if solution is None:
        raise RuntimeError("OR-Tools returned no solution (INFEASIBLE)")

    routes: list[Route] = []
    assigned: set[int] = set()
    for v in range(team_size):
        index = routing.Start(v)
        stops: list[RouteStop] = []
        prev_node = 0
        time_used = 0
        distance_km = 0.0
        kg_used = 0.0
        seq = 0
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != 0:
                seq += 1
                d = distance_matrix[prev_node][node] / 1000.0
                travel_min = int(d / speed_kmh * 60.0)
                arrive = time_used + travel_min
                depart = arrive + service_minutes_per_stop
                h = hotspots[node - 1]
                stops.append(
                    RouteStop(
                        seq=seq, lat=h.lat, lng=h.lng,
                        hotspot_id=h.hotspot_id or f"hp-{node}",
                        arrive=_format_min(8 * 60, arrive),
                        depart=_format_min(8 * 60, depart),
                        est_kg=h.est_kg, p_exceed=h.probability,
                    )
                )
                distance_km += d
                kg_used += h.est_kg
                time_used = depart
                assigned.add(node - 1)
                prev_node = node
            index = solution.Value(routing.NextVar(index))
        # return to depot
        end_node = manager.IndexToNode(index)
        distance_km += distance_matrix[prev_node][end_node] / 1000.0
        routes.append(
            Route(
                team_id=v + 1, stops=stops,
                total_distance_km=round(distance_km, 2),
                total_time_min=int(time_used),
                total_kg_est=round(kg_used, 1),
            )
        )
    unassigned = [
        hotspots[i].hotspot_id or f"hp-{i + 1}"
        for i in range(len(hotspots))
        if i not in assigned
    ]
    total_kg = sum(r.total_kg_est for r in routes)
    return VrpResult(
        routes=routes, unassigned_hotspots=unassigned,
        total_kg_est=round(total_kg, 1),
        solver_status="OPTIMAL" if not unassigned else "FEASIBLE",
        solve_time_ms=elapsed_ms,
    )
