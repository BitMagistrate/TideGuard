"""Feature-gate — table of which tier may call which endpoint.

The plan defines four billing categories (api / b2g / esg / adopt). The
gate exposes a single ``check_access`` function consumed by the
``TierEnforcementMiddleware`` and works equally well when the database
``tiers`` row exists (preferred) or when it does not (in which case we
fall back to the static ``TIERS`` constant below). Keeping a hardcoded
fallback means tests can run without a populated database and the
service degrades gracefully if a row is deleted.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Static tier table — mirror of ``apps/web/lib/tiers.ts``.  Numbers come from
# the Monetization Implementation Plan §2.1.
# ---------------------------------------------------------------------------

TIERS: dict[str, dict[str, Any]] = {
    # -- API tiers --
    "free": {
        "category": "api",
        "display_name": "Free",
        "price_monthly_usd": 0,
        "monthly_quota": 1_000,
        "rps": 1,
        "regions": ["black_sea"],
        "allow_archive_years": 0,
        "allow_ogc": False,
        "attribution_required": True,
        "allow_endpoints": ["/forecast", "/forecast/exceedance", "/cleanup_planner"],
    },
    "pro": {
        "category": "api",
        "display_name": "Pro",
        "price_monthly_usd": 49,
        "monthly_quota": 10_000,
        "rps": 10,
        "regions": ["black_sea", "caspian", "baltic"],
        "allow_archive_years": 0,
        "allow_ogc": False,
        "attribution_required": False,
        "allow_endpoints": ["/forecast/*", "/cleanup_planner", "/forecast"],
    },
    "business": {
        "category": "api",
        "display_name": "Business",
        "price_monthly_usd": 299,
        "monthly_quota": 100_000,
        "rps": 100,
        "regions": ["*"],
        "allow_archive_years": 5,
        "allow_ogc": True,
        "attribution_required": False,
        "allow_endpoints": ["/forecast/*", "/cleanup_planner", "/ogc/*", "/b2g/*"],
        "email_support_sla_hours": 24,
    },
    "enterprise": {
        "category": "api",
        "display_name": "Enterprise",
        "price_monthly_usd": 999,
        "monthly_quota": None,
        "rps": None,
        "regions": ["*"],
        "allow_archive_years": None,
        "allow_ogc": True,
        "attribution_required": False,
        "on_premise": True,
        "sso": True,
        "phone_support": True,
        "sla_uptime_pct": 99.9,
        "allow_endpoints": ["*"],
    },
    # -- B2G tiers --
    "b2g_basic": {
        "category": "b2g",
        "display_name": "B2G Basic",
        "price_monthly_usd": 200,
        "monthly_quota": None,
        "rps": 10,
        "regions": ["*"],
        "allow_endpoints": ["/b2g/*", "/forecast/*", "/cleanup_planner"],
    },
    "b2g_pro": {
        "category": "b2g",
        "display_name": "B2G Pro",
        "price_monthly_usd": 500,
        "monthly_quota": None,
        "rps": 30,
        "regions": ["*"],
        "allow_endpoints": ["/b2g/*", "/forecast/*", "/cleanup_planner"],
    },
    # -- ESG --
    "esg_insurance": {
        "category": "esg",
        "display_name": "ESG Insurance",
        "price_monthly_usd": 1500,
        "monthly_quota": 10_000,
        "rps": 30,
        "regions": ["*"],
        "allow_endpoints": ["/esg/*", "/forecast/*"],
    },
    "esg_sponsorship": {
        "category": "esg",
        "display_name": "ESG Sponsorship",
        "price_monthly_usd": 1500,
        "monthly_quota": 1_000,
        "rps": 5,
        "regions": ["*"],
        "allow_endpoints": ["/esg/*", "/impact"],
    },
    "esg_hotel": {
        "category": "esg",
        "display_name": "ESG Hotel / Widget",
        "price_monthly_usd": 750,
        "monthly_quota": 100_000,  # widget hits are cheap
        "rps": 30,
        "regions": ["*"],
        "allow_endpoints": ["/widgets/*", "/forecast/*"],
    },
    # -- Adopt --
    "adopt_individual": {
        "category": "adopt",
        "display_name": "Adopt — Individual",
        "price_monthly_usd": 5,
        "monthly_quota": 1_000,
        "rps": 5,
        "regions": ["*"],
        "allow_endpoints": ["/adopt/*", "/forecast/*"],
    },
    "adopt_business": {
        "category": "adopt",
        "display_name": "Adopt — Business",
        "price_monthly_usd": 50,
        "monthly_quota": 10_000,
        "rps": 10,
        "regions": ["*"],
        "allow_endpoints": ["/adopt/*", "/widgets/*", "/forecast/*"],
    },
}


@dataclass(slots=True)
class AccessDecision:
    allow: bool
    reason: str = "ok"
    requires_attribution: bool = False
    tier_features: dict[str, Any] | None = None


def _match_endpoint(path: str, patterns: list[str]) -> bool:
    if not patterns:
        return False
    for p in patterns:
        if p == "*":
            return True
        if fnmatch.fnmatch(path, p):
            return True
        # Treat trailing /* like a prefix (e.g. /b2g/* matches /b2g/dashboard/regions/...)
        if p.endswith("/*") and path.startswith(p[:-2]):
            return True
        if p == path:
            return True
    return False


def get_tier(tier_slug: str | None) -> dict[str, Any]:
    if not tier_slug:
        return TIERS["free"]
    return TIERS.get(tier_slug, TIERS["free"])


def check_access(
    tier_slug: str | None,
    endpoint: str,
    params: dict[str, Any] | None = None,
) -> AccessDecision:
    """Return an :class:`AccessDecision` for the given (tier, endpoint, params)."""
    tier = get_tier(tier_slug)
    allow_endpoints: list[str] = tier.get("allow_endpoints", [])

    if not _match_endpoint(endpoint, allow_endpoints):
        return AccessDecision(
            allow=False,
            reason="tier_too_low",
            requires_attribution=tier.get("attribution_required", False),
            tier_features=tier,
        )

    # OGC gating
    if endpoint.startswith("/ogc/") and not tier.get("allow_ogc", False):
        return AccessDecision(allow=False, reason="ogc_requires_upgrade", tier_features=tier)

    # Archive-year gating (years parameter).
    if params and "years" in params:
        try:
            years = int(params["years"])
        except (TypeError, ValueError):
            years = 0
        max_years = tier.get("allow_archive_years", 0)
        if max_years is not None and years > max_years:
            return AccessDecision(allow=False, reason="archive_window_too_large", tier_features=tier)

    # Region gating — bbox vs allowed regions (lightweight: domain name only).
    allowed_regions: list[str] = tier.get("regions", [])
    if allowed_regions and allowed_regions != ["*"] and params:
        region = params.get("region")
        if region and region not in allowed_regions:
            return AccessDecision(allow=False, reason="region_not_allowed", tier_features=tier)

    return AccessDecision(
        allow=True,
        reason="ok",
        requires_attribution=tier.get("attribution_required", False),
        tier_features=tier,
    )


_PATH_NORMALISE = re.compile(r"/[0-9a-fA-F-]{16,}")


def normalise_endpoint(path: str) -> str:
    """Strip trailing UUIDs / segment ids so usage aggregates collapse properly."""
    return _PATH_NORMALISE.sub("/{id}", path).rstrip("/") or "/"
