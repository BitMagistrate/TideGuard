"""Geometry helpers for the Adopt-a-Beach block (§6).

Cuts a coastline LINESTRING into ~1 km segments and exposes utilities for
mid-point calculation and bbox filtering.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(slots=True)
class Segment:
    slug: str
    geom_wkt: str
    length_m: float
    midpoint_lat: float
    midpoint_lng: float
    display_name: str


_EARTH_R = 6_371_000.0


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return _EARTH_R * 2 * math.asin(math.sqrt(h))


def _interp(a: tuple[float, float], b: tuple[float, float], t: float) -> tuple[float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def slice_coastline(
    coords: list[tuple[float, float]],
    segment_length_m: float = 1000.0,
    name_prefix: str = "beach",
) -> list[Segment]:
    """Walk along ``coords`` (a polyline of (lat, lng) pairs) and emit
    fixed-length segments until the line is exhausted.

    Returns a list of :class:`Segment` objects with WKT LINESTRING geometry.
    """
    if len(coords) < 2:
        return []

    segments: list[Segment] = []
    current_segment: list[tuple[float, float]] = [coords[0]]
    remaining = segment_length_m
    counter = 1

    for i in range(1, len(coords)):
        a = current_segment[-1]
        b = coords[i]
        leg = haversine_m(a, b)
        while leg >= remaining and leg > 0:
            t = remaining / leg
            mid = _interp(a, b, t)
            current_segment.append(mid)
            segments.append(_finalise(current_segment, name_prefix, counter))
            counter += 1
            # restart from the midpoint
            current_segment = [mid]
            a = mid
            leg = haversine_m(a, b)
            remaining = segment_length_m
        current_segment.append(b)
        remaining -= leg
    if len(current_segment) >= 2 and haversine_m(current_segment[0], current_segment[-1]) > 100:
        segments.append(_finalise(current_segment, name_prefix, counter))
    return segments


def _finalise(points: list[tuple[float, float]], prefix: str, idx: int) -> Segment:
    # midpoint by arc length
    total = 0.0
    distances = [0.0]
    for i in range(1, len(points)):
        total += haversine_m(points[i - 1], points[i])
        distances.append(total)
    target = total / 2.0
    mid_lat, mid_lng = points[0]
    for i in range(1, len(points)):
        if distances[i] >= target:
            ratio = 0.0 if distances[i] == distances[i - 1] else (target - distances[i - 1]) / (
                distances[i] - distances[i - 1]
            )
            mid_lat, mid_lng = _interp(points[i - 1], points[i], ratio)
            break
    wkt_points = ", ".join(f"{lng} {lat}" for lat, lng in points)
    wkt = f"LINESTRING ({wkt_points})"
    return Segment(
        slug=f"{prefix}-{idx:03d}",
        geom_wkt=wkt,
        length_m=round(total, 1),
        midpoint_lat=mid_lat,
        midpoint_lng=mid_lng,
        display_name=f"{prefix.title()}: segment {idx}",
    )


def bbox_filter(segments: Iterable[Segment], bbox: tuple[float, float, float, float]) -> list[Segment]:
    lon_min, lat_min, lon_max, lat_max = bbox
    return [
        s for s in segments
        if lon_min <= s.midpoint_lng <= lon_max and lat_min <= s.midpoint_lat <= lat_max
    ]


def synthetic_coast_for_bbox(
    bbox: tuple[float, float, float, float],
    step_deg: float = 0.02,
    waviness: float = 0.005,
) -> list[tuple[float, float]]:
    """A deterministic synthetic coastline for seeding when OSM isn't
    accessible. Produces a sine-wavy polyline tracing the south edge of
    the bbox so the slicer can chew on it.
    """
    lon_min, lat_min, lon_max, _lat_max = bbox
    coords: list[tuple[float, float]] = []
    lon = lon_min
    i = 0
    while lon <= lon_max:
        lat = lat_min + waviness * math.sin(i * 0.5)
        coords.append((lat, lon))
        lon += step_deg
        i += 1
    return coords
