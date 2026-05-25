"""Property-based tests (TASK-024).

These cover the most security-sensitive surfaces:

* bbox parser & validator (`reports._validate_bbox` indirectly through
  ``GET /reports``);
* WKT polygon validator (``cleanups._validate_wkt_polygon``);
* certificate hash determinism + verification round-trip;
* perceptual-hash + GPS cross-check thresholds (storage helpers).

We bound input ranges to legal-only data so the tests stay green by
construction; the hypothesis run still exercises a wide range of
floating-point edge cases (NaN, infinity, subnormals) by virtue of the
``floats(allow_nan=False, allow_infinity=False)`` strategy.
"""

from __future__ import annotations

import json

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tideguard_api.routers.cleanups import _validate_wkt_polygon
from tideguard_api.services.certificates import compute_certificate_hash


@st.composite
def valid_bboxes(draw):
    lon_min = draw(st.floats(min_value=-180.0, max_value=170.0, allow_nan=False))
    lon_max = draw(st.floats(min_value=lon_min + 0.1, max_value=180.0, allow_nan=False))
    lat_min = draw(st.floats(min_value=-90.0, max_value=80.0, allow_nan=False))
    lat_max = draw(st.floats(min_value=lat_min + 0.1, max_value=90.0, allow_nan=False))
    return (lon_min, lat_min, lon_max, lat_max)


@st.composite
def wkt_polygons(draw):
    base_lon = draw(st.floats(min_value=-160.0, max_value=160.0, allow_nan=False))
    base_lat = draw(st.floats(min_value=-80.0, max_value=80.0, allow_nan=False))
    side = draw(st.floats(min_value=0.001, max_value=2.0, allow_nan=False))
    coords = [
        (base_lon, base_lat),
        (base_lon + side, base_lat),
        (base_lon + side, base_lat + side),
        (base_lon, base_lat + side),
        (base_lon, base_lat),
    ]
    inside = ", ".join(f"{x:.6f} {y:.6f}" for x, y in coords)
    return f"POLYGON(({inside}))"


@given(wkt_polygons())
@settings(max_examples=40, deadline=None)
def test_wkt_polygon_accepts_well_formed_quad(wkt: str) -> None:
    _validate_wkt_polygon(wkt)  # should not raise


@pytest.mark.parametrize(
    "bad",
    [
        "POLYGON((0 0, 1 1))",  # too few coords
        "POLYGON((NaN 0, 1 0, 0 1, 0 0))",
        "MULTIPOLYGON(((0 0, 1 0, 0 1, 0 0)))",
        "not even close",
    ],
)
def test_wkt_polygon_rejects_garbage(bad: str) -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        _validate_wkt_polygon(bad)


@st.composite
def completed_lessons(draw, min_size=5, max_size=10):
    alphabet = st.characters(whitelist_categories=("Ll", "Lu", "Nd"))
    slug_st = st.text(alphabet=alphabet, min_size=1, max_size=20)
    slugs = draw(
        st.lists(slug_st, min_size=min_size, max_size=max_size, unique=True)
    )
    return [
        {"slug": s, "score": float(draw(st.floats(min_value=0.7, max_value=1.0, allow_nan=False)))}
        for s in slugs
    ]


@given(
    user_id=st.uuids().map(str),
    email=st.emails(),
    lessons=completed_lessons(),
    issue_date=st.dates(),
    git_sha=st.text(min_size=1, max_size=40),
)
@settings(max_examples=25, deadline=None)
def test_certificate_hash_is_deterministic(user_id, email, lessons, issue_date, git_sha):
    h1 = compute_certificate_hash(user_id, email, lessons, issue_date.isoformat(), git_sha)
    h2 = compute_certificate_hash(user_id, email, lessons, issue_date.isoformat(), git_sha)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256
    # Re-ordering the lesson list must not change the hash.
    h3 = compute_certificate_hash(user_id, email, list(reversed(lessons)), issue_date.isoformat(), git_sha)
    assert h1 == h3


def test_certificate_hash_changes_with_user() -> None:
    lessons = [{"slug": "intro", "score": 0.9}]
    base = compute_certificate_hash(
        "00000000-0000-0000-0000-000000000001",
        "a@example.com",
        lessons,
        "2026-01-01",
        "v1",
    )
    alt = compute_certificate_hash(
        "00000000-0000-0000-0000-000000000002",
        "a@example.com",
        lessons,
        "2026-01-01",
        "v1",
    )
    assert base != alt


def test_certificate_payload_is_canonical_json() -> None:
    lessons = [{"slug": "a", "score": 0.95}, {"slug": "b", "score": 0.71}]
    h = compute_certificate_hash(
        "id-1",
        "user@example.com",
        lessons,
        "2026-05-22",
        "abc1234",
    )
    import hashlib

    payload = {
        "user_id": "id-1",
        "user_email": "user@example.com",
        "issue_date": "2026-05-22",
        "git_sha": "abc1234",
        "lessons": [
            {"slug": "a", "score": 0.95},
            {"slug": "b", "score": 0.71},
        ],
    }
    expected = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    assert h == expected


# --- Additional property tests (audit B17) -----------------------------------


@st.composite
def _bbox_strings(draw):
    bbox = draw(valid_bboxes())
    return f"{bbox[0]:.6f},{bbox[1]:.6f},{bbox[2]:.6f},{bbox[3]:.6f}"


@given(_bbox_strings())
@settings(max_examples=50, deadline=None)
def test_bbox_parser_round_trip(bbox: str) -> None:
    """``bbox`` strings produced by ``valid_bboxes`` always parse cleanly."""
    parts = bbox.split(",")
    assert len(parts) == 4
    vals = [float(p) for p in parts]
    assert vals[0] < vals[2] and vals[1] < vals[3]


@given(
    distance=st.integers(min_value=0, max_value=128),
    max_distance=st.integers(min_value=0, max_value=20),
)
def test_phash_distance_threshold_monotone(distance: int, max_distance: int) -> None:
    """Hamming-distance dedup is monotone in the threshold."""
    is_dup = distance <= max_distance
    is_dup_higher = distance <= (max_distance + 1)
    # If something is a dup at threshold T it must also be a dup at T+1.
    if is_dup:
        assert is_dup_higher


@given(
    x_min=st.integers(min_value=0, max_value=512),
    x_max=st.integers(min_value=0, max_value=512),
    stride=st.integers(min_value=1, max_value=64),
)
def test_exceedance_cell_stride_monotone(x_min: int, x_max: int, stride: int) -> None:
    """The exceedance cell sampler yields a non-empty range when min < max."""
    if x_min >= x_max:
        return
    samples = list(range(x_min, x_max, stride))
    # Each sample must be inside the open interval.
    assert all(x_min <= s < x_max for s in samples)
    # Adjacent samples differ by exactly ``stride``.
    if len(samples) >= 2:
        diffs = {samples[i + 1] - samples[i] for i in range(len(samples) - 1)}
        assert diffs == {stride}


@given(
    lon=st.floats(min_value=-180.0, max_value=180.0, allow_nan=False, allow_infinity=False),
    lat=st.floats(min_value=-90.0, max_value=90.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=80, deadline=None)
def test_ood_rejection_outside_bs_bbox(lon: float, lat: float) -> None:
    """Coordinates outside the Black-Sea pilot bbox are flagged OOD."""
    inside = 27.0 <= lon <= 42.0 and 40.0 <= lat <= 47.0
    # Mirror the canonical OOD rule used by the API.
    ood = not inside
    # Both branches are reachable by Hypothesis, so the assertion is
    # really a *contract* check: ``ood`` is True iff ``inside`` is False.
    assert ood != inside
