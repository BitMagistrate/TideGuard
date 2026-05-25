"""/developers — public-developer-portal stub.

In v0.4 the API is in *public-beta*: keys are not yet enforced for `/forecast`
to avoid raising friction during the demo, but the portal documents the
roadmap (`X-API-Key` header) and exposes ready-to-paste curl examples.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/developers", tags=["developers"])


@router.get("")
def developer_portal() -> JSONResponse:
    """Return the public TideGuard API contract + curl recipes."""
    return JSONResponse(
        {
            "title": "TideGuard Developer Portal",
            "status": "public-beta",
            "base_url": "https://api.tideguard.app",
            "auth": {
                "header": "X-API-Key",
                "enforcement": "soft (rate-limited, anonymous OK)",
                "request_a_key": "mailto:contact@tideguard.app?subject=API%20key%20request",
            },
            "rate_limits": {
                "anonymous": "60 requests / minute (slowapi)",
                "with_key": "600 requests / minute",
            },
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/forecast?bbox=27,40,42,47&horizon=7",
                    "summary": "PINN forecast on a 24×24 grid (D+0…D+13).",
                    "example": "curl 'https://api.tideguard.app/forecast?bbox=27,40,42,47&horizon=7'",
                },
                {
                    "method": "GET",
                    "path": "/forecast/exceedance?bbox=27,40,42,47&horizon=7&quantile=0.9",
                    "summary": "Per-pixel probability of exceeding the 90th-percentile concentration.",
                    "example": "curl 'https://api.tideguard.app/forecast/exceedance?bbox=27,40,42,47&quantile=0.95'",
                },
                {
                    "method": "GET",
                    "path": "/forecast/explain?lat=44.5&lng=37.8&horizon=7",
                    "summary": "Physical decomposition of the prediction at a point.",
                    "example": "curl 'https://api.tideguard.app/forecast/explain?lat=44.5&lng=37.8&horizon=7'",
                },
                {
                    "method": "GET",
                    "path": "/forecast/backward?lat=44.0&lng=37.5&days_back=14",
                    "summary": "Reverse trajectory: where did the plastic come from?",
                    "example": "curl 'https://api.tideguard.app/forecast/backward?lat=44.0&lng=37.5&days_back=14'",
                },
                {
                    "method": "GET",
                    "path": "/forecast/counterfactual?bbox=27,40,42,47&horizon=7&modify=wind*0.5",
                    "summary": "What-if scenarios: scale a physics knob and see the delta.",
                    "example": "curl 'https://api.tideguard.app/forecast/counterfactual?modify=disable_windage'",
                },
                {
                    "method": "GET",
                    "path": "/forecast/active_learning?bbox=27,40,42,47&horizon=7&k=5",
                    "summary": "BALD-ranked cells where a new citizen report most reduces uncertainty.",
                    "example": "curl 'https://api.tideguard.app/forecast/active_learning?k=10'",
                },
                {
                    "method": "GET",
                    "path": "/cleanup_planner?bbox=37.4,44.0,38.0,44.6&team_size=10&horizon=7",
                    "summary": "Best day-and-time-window for a coastal cleanup at the given bbox.",
                    "example": "curl 'https://api.tideguard.app/cleanup_planner?team_size=20'",
                },
                {
                    "method": "GET",
                    "path": "/ogc/wms?service=WMS&request=GetCapabilities",
                    "summary": "OGC WMS 1.3.0 endpoint (QGIS / ArcGIS compatible).",
                    "example": "curl 'https://api.tideguard.app/ogc/wms?service=WMS&request=GetCapabilities'",
                },
                {
                    "method": "GET",
                    "path": "/ogc/stac/catalog.json",
                    "summary": "SpatioTemporal Asset Catalog (STAC 1.0.0) root.",
                    "example": "curl 'https://api.tideguard.app/ogc/stac/catalog.json'",
                },
                {
                    "method": "GET",
                    "path": "/ogc/geojson?bbox=27,40,42,47&horizon=7",
                    "summary": "GeoJSON FeatureCollection export of the final-day grid.",
                    "example": (
                        "curl 'https://api.tideguard.app/ogc/geojson?bbox=27,40,42,47"
                        "&horizon=7' > tideguard.geojson"
                    ),
                },
                {
                    "method": "GET",
                    "path": "/sustainability/footprint",
                    "summary": "Live carbon ledger (kWh, kg CO2e, plastic-prevented mass).",
                    "example": "curl 'https://api.tideguard.app/sustainability/footprint?period_days=30'",
                },
            ],
            "openapi": "/openapi.json",
            "github": "https://github.com/desirewarlockstaple/mnohyjmg",
            "zenodo": "10.5281/zenodo.<TBD>",
        }
    )
