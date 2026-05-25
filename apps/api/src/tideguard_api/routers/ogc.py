"""OGC interoperability: WMS GetCapabilities/GetMap + STAC catalog + GeoJSON.

This makes TideGuard forecasts consumable from QGIS / ArcGIS / Google Earth
Engine without any TideGuard-specific code on the client side. The STAC
endpoint also positions the project on the same shelf as
NASA EarthData / Microsoft Planetary Computer.
"""

from __future__ import annotations

import io
from datetime import UTC, date, datetime

import numpy as np
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from PIL import Image

from tideguard_api.services.inference import predict_forecast

router = APIRouter(prefix="/ogc", tags=["ogc"])


_WMS_CAPABILITIES = """<?xml version="1.0" encoding="UTF-8"?>
<WMS_Capabilities version="1.3.0" xmlns="http://www.opengis.net/wms">
  <Service>
    <Name>WMS</Name>
    <Title>TideGuard AI — marine debris forecast</Title>
    <Abstract>Physics-Informed Neural Network forecasts of floating
    debris concentration over the Black Sea. Pilot region:
    27,40,42,47.</Abstract>
    <KeywordList>
      <Keyword>marine-debris</Keyword>
      <Keyword>physics-informed-neural-network</Keyword>
      <Keyword>Black-Sea</Keyword>
      <Keyword>SDG14</Keyword>
    </KeywordList>
    <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink"
                    xlink:type="simple"
                    xlink:href="https://api.tideguard.app/ogc/wms"/>
  </Service>
  <Capability>
    <Request>
      <GetCapabilities>
        <Format>application/vnd.ogc.wms_xml</Format>
        <DCPType><HTTP><Get><OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink"
          xlink:href="https://api.tideguard.app/ogc/wms?service=WMS&amp;request=GetCapabilities"/></Get></HTTP></DCPType>
      </GetCapabilities>
      <GetMap>
        <Format>image/png</Format>
        <DCPType><HTTP><Get><OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink"
          xlink:href="https://api.tideguard.app/ogc/wms"/></Get></HTTP></DCPType>
      </GetMap>
    </Request>
    <Layer>
      <Name>tideguard:concentration_d7</Name>
      <Title>TideGuard PINN — concentration D+7</Title>
      <CRS>EPSG:4326</CRS>
      <CRS>CRS:84</CRS>
      <EX_GeographicBoundingBox>
        <westBoundLongitude>27</westBoundLongitude>
        <eastBoundLongitude>42</eastBoundLongitude>
        <southBoundLatitude>40</southBoundLatitude>
        <northBoundLatitude>47</northBoundLatitude>
      </EX_GeographicBoundingBox>
    </Layer>
  </Capability>
</WMS_Capabilities>"""


def _palette(value: float) -> tuple[int, int, int, int]:
    """Same diverging palette used by /tiles."""
    v = max(0.0, min(1.0, value))
    if v < 0.25:
        return (66, 165, 245, 200)
    if v < 0.5:
        return (102, 187, 106, 200)
    if v < 0.75:
        return (255, 167, 38, 220)
    return (244, 67, 54, 240)


def _render_layer_png(
    lon_min: float, lat_min: float, lon_max: float, lat_max: float,
    width: int, height: int, day_index: int,
) -> bytes:
    forecast = predict_forecast(lon_min, lon_max, lat_min, lat_max, horizon_days=14)
    day = forecast.days[min(day_index, len(forecast.days) - 1)]
    # build a coarse raster from the cell list
    side = int(round(len(day.cells) ** 0.5))
    arr = np.array([c.concentration for c in day.cells], dtype=np.float32).reshape(side, side)
    img = np.zeros((height, width, 4), dtype=np.uint8)
    for j in range(height):
        sy = int(j * side / height)
        for i in range(width):
            sx = int(i * side / width)
            img[j, i] = _palette(float(arr[sy, sx]))
    out = Image.fromarray(img, mode="RGBA")
    out = out.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return buf.getvalue()


@router.get("/wms")
def wms(
    service: str = Query(..., alias="service"),
    request: str = Query(..., alias="request"),
    layers: str | None = Query(None),
    bbox: str | None = Query(None),
    width: int = Query(256, ge=16, le=4096),
    height: int = Query(256, ge=16, le=4096),
    format: str = Query("image/png"),  # noqa: A002
    crs: str | None = Query("EPSG:4326", alias="crs"),
) -> Response:
    """Minimal WMS 1.3.0 endpoint."""
    if service.upper() != "WMS":
        raise HTTPException(400, "service must be 'WMS'")
    req = request.upper()
    if req == "GETCAPABILITIES":
        return Response(content=_WMS_CAPABILITIES, media_type="application/vnd.ogc.wms_xml")
    if req == "GETMAP":
        if not layers or not bbox:
            raise HTTPException(400, "layers and bbox are required for GetMap")
        try:
            west, south, east, north = (float(x) for x in bbox.split(","))
        except Exception as exc:
            raise HTTPException(400, f"Invalid bbox: {exc}") from exc
        # layer name encodes the horizon day: tideguard:concentration_d{N}
        day_index = 6
        if ":" in layers:
            tag = layers.split(":", 1)[1]
            if tag.startswith("concentration_d"):
                try:
                    day_index = int(tag.removeprefix("concentration_d")) - 1
                except ValueError:
                    pass
        png = _render_layer_png(west, south, east, north, width, height, day_index)
        if not format.lower().startswith("image/png"):
            raise HTTPException(400, "only image/png is implemented")
        return Response(content=png, media_type="image/png")
    raise HTTPException(400, f"unsupported WMS request '{request}'")


@router.get("/stac/catalog.json")
def stac_catalog() -> JSONResponse:
    """STAC root catalog."""
    return JSONResponse(
        {
            "type": "Catalog",
            "id": "tideguard-ai",
            "stac_version": "1.0.0",
            "description": "TideGuard AI — marine debris PINN forecasts (Black Sea pilot).",
            "title": "TideGuard AI STAC catalog",
            "license": "CC-BY-4.0",
            "links": [
                {"rel": "root", "href": "/ogc/stac/catalog.json", "type": "application/json"},
                {"rel": "self", "href": "/ogc/stac/catalog.json", "type": "application/json"},
                {
                    "rel": "child",
                    "href": "/ogc/stac/collections/concentration",
                    "type": "application/json",
                    "title": "Surface debris concentration",
                },
            ],
        }
    )


@router.get("/stac/collections/concentration")
def stac_collection_concentration() -> JSONResponse:
    today = date.today().isoformat()
    return JSONResponse(
        {
            "type": "Collection",
            "stac_version": "1.0.0",
            "id": "concentration",
            "title": "TideGuard PINN concentration (Black Sea)",
            "description": "Forecast of floating debris concentration on a 24×24 grid.",
            "license": "CC-BY-4.0",
            "extent": {
                "spatial": {"bbox": [[27, 40, 42, 47]]},
                "temporal": {"interval": [["2024-01-01T00:00:00Z", None]]},
            },
            "summaries": {
                "horizon_days": [1, 14],
                "model_version": ["tideguard-pinn-v0.4"],
            },
            "links": [
                {"rel": "self", "href": "/ogc/stac/collections/concentration"},
                {"rel": "parent", "href": "/ogc/stac/catalog.json"},
                {"rel": "items", "href": f"/ogc/stac/collections/concentration/items?date={today}"},
            ],
        }
    )


@router.get("/stac/collections/concentration/items")
def stac_items(
    date_iso: str | None = Query(None, alias="date"),
) -> JSONResponse:
    iso = date_iso or date.today().isoformat()
    when = datetime.now(UTC).replace(microsecond=0).isoformat()
    return JSONResponse(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": f"tideguard-pinn-{iso}-d7",
                    "stac_version": "1.0.0",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [27, 40], [42, 40], [42, 47], [27, 47], [27, 40],
                        ]],
                    },
                    "bbox": [27, 40, 42, 47],
                    "properties": {
                        "datetime": when,
                        "as_of_date": iso,
                        "horizon_days": 7,
                        "model_version": "tideguard-pinn-v0.4",
                    },
                    "assets": {
                        "preview": {
                            "type": "image/png",
                            "href": (
                                "/ogc/wms?service=WMS&request=GetMap"
                                "&layers=tideguard:concentration_d7"
                                "&bbox=27,40,42,47&width=512&height=512&format=image/png"
                            ),
                            "title": "PNG preview",
                        },
                        "json": {
                            "type": "application/json",
                            "href": "/forecast?bbox=27,40,42,47&horizon=7",
                            "title": "Raw JSON",
                        },
                        "geojson": {
                            "type": "application/geo+json",
                            "href": "/ogc/geojson?bbox=27,40,42,47&horizon=7",
                            "title": "GeoJSON FeatureCollection",
                        },
                    },
                }
            ],
        }
    )


@router.get("/geojson")
def geojson_export(
    bbox: str = Query("27,40,42,47"),
    horizon: int = Query(7, ge=1, le=14),
) -> JSONResponse:
    """Standard GeoJSON FeatureCollection export of the forecast grid."""
    try:
        lon_min, lat_min, lon_max, lat_max = (float(x) for x in bbox.split(","))
    except Exception as exc:
        raise HTTPException(400, f"Invalid bbox: {exc}") from exc
    forecast = predict_forecast(lon_min, lon_max, lat_min, lat_max, horizon_days=horizon)
    day = forecast.days[-1]
    features = []
    for c in day.cells:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [c.lng, c.lat]},
                "properties": {
                    "concentration": c.concentration,
                    "day": day.day,
                    "model_version": forecast.model_version,
                },
            }
        )
    return JSONResponse(
        {
            "type": "FeatureCollection",
            "name": "tideguard-forecast",
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "metadata": {
                "bbox": forecast.bbox,
                "horizon_days": forecast.horizon_days,
                "model_version": forecast.model_version,
            },
            "features": features,
        }
    )


@router.get("/robots.txt")
def robots() -> PlainTextResponse:
    """A friendly machine-readable note pointing crawlers at the STAC catalog."""
    return PlainTextResponse(
        "User-agent: *\nAllow: /ogc/\nSitemap: /ogc/stac/catalog.json\n"
    )
