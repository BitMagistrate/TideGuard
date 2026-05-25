"""Tests for the feature-gate decision table."""

from __future__ import annotations

import pytest

from tideguard_api.services.feature_gate import check_access, get_tier, normalise_endpoint


@pytest.mark.parametrize(
    "tier, endpoint, expected_allow",
    [
        ("free", "/forecast", True),
        ("free", "/ogc/wms", False),
        ("free", "/b2g/dashboard/regions", False),
        ("pro", "/forecast/exceedance", True),
        ("pro", "/ogc/wms", False),
        ("business", "/ogc/wms", True),
        ("business", "/b2g/dashboard/regions", True),
        ("enterprise", "/anything", True),
        ("esg_insurance", "/esg/insurance/risk", True),
        ("esg_insurance", "/b2g/routing/solve", False),
        ("b2g_basic", "/b2g/dashboard/regions/sochi/summary", True),
        ("adopt_individual", "/adopt/segments", True),
    ],
)
def test_tier_endpoint_matrix(tier, endpoint, expected_allow):
    decision = check_access(tier, endpoint)
    assert decision.allow is expected_allow, f"{tier} × {endpoint} → expected {expected_allow}, got {decision}"


def test_attribution_required_for_free_tier():
    decision = check_access("free", "/forecast")
    assert decision.requires_attribution is True


def test_normalise_endpoint_strips_ids():
    assert normalise_endpoint("/adopt/segments/abcdef1234567890") == "/adopt/segments/{id}"
    assert normalise_endpoint("/adopt/segments/") == "/adopt/segments"
    assert normalise_endpoint("") == "/"


def test_free_tier_historical_blocked():
    decision = check_access("free", "/forecast/historical", params={"years": 5})
    assert decision.allow is False
    assert decision.reason in ("archive_window_too_large", "tier_too_low")


def test_get_tier_returns_quota():
    tier = get_tier("pro")
    assert tier["monthly_quota"] > 0
