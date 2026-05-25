"""Tests for the coastline-slicing geometry helpers."""

from __future__ import annotations

from tideguard_api.services.geometry import (
    bbox_filter,
    haversine_m,
    slice_coastline,
    synthetic_coast_for_bbox,
)


def test_haversine_zero_distance():
    assert haversine_m((44.0, 39.0), (44.0, 39.0)) == 0.0


def test_haversine_approx_paris_london():
    # Paris (48.85, 2.35) <-> London (51.51, -0.13) ≈ 344 km
    d_km = haversine_m((48.85, 2.35), (51.51, -0.13)) / 1000
    assert 330 < d_km < 360


def test_slice_coastline_produces_sub_kilometre_segments():
    coords = [(44.0, 39.0 + i * 0.01) for i in range(20)]
    segs = slice_coastline(coords, segment_length_m=1000.0, name_prefix="x")
    assert all(900 <= s.length_m <= 1100 for s in segs[:-1])
    assert all(s.slug.startswith("x-") for s in segs)


def test_synthetic_coast_in_bbox():
    bbox = (37.2, 44.79, 37.55, 44.99)
    coords = synthetic_coast_for_bbox(bbox)
    assert len(coords) > 1
    assert all(37.2 - 0.01 <= lon <= 37.55 + 0.01 for _lat, lon in coords)


def test_bbox_filter():
    coords = synthetic_coast_for_bbox((37.2, 44.79, 37.55, 44.99))
    segs = slice_coastline(coords, segment_length_m=1000.0, name_prefix="x")
    inside = bbox_filter(segs, (37.0, 44.7, 37.6, 45.0))
    assert len(inside) == len(segs)
    outside = bbox_filter(segs, (0.0, 0.0, 0.1, 0.1))
    assert outside == []
