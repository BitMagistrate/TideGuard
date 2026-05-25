"use client";

import maplibregl from "maplibre-gl";
import { useEffect, useRef } from "react";
import "maplibre-gl/dist/maplibre-gl.css";

import { fetchExceedance } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Black-Sea defaults (TASK-011 / CRIT-WEB-1). Previous build was centred on
// Taiwan, which made the demo confusing for jurors and made the API reject
// every initial request as out-of-domain.
const BLACK_SEA_BBOX: [number, number, number, number] = [27, 40, 42, 47];
const BLACK_SEA_CENTER: [number, number] = [
  (BLACK_SEA_BBOX[0] + BLACK_SEA_BBOX[2]) / 2,
  (BLACK_SEA_BBOX[1] + BLACK_SEA_BBOX[3]) / 2,
];
const BLACK_SEA_ZOOM = 5.5;

// ESRI World Imagery — satellite tiles with no political admin labels.
// Chosen for politically-neutral rendering of contested basins (Black Sea etc.).
// Free for non-commercial use with attribution per the ESRI ArcGIS Online ToS.
const FALLBACK_STYLE = {
  version: 8 as const,
  sources: {
    esri: {
      type: "raster" as const,
      tiles: [
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      ],
      tileSize: 256,
      maxzoom: 19,
      attribution:
        "Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, USDA FSA, USGS, AeroGRID, IGN, and the GIS User Community",
    },
  },
  layers: [{ id: "esri", type: "raster" as const, source: "esri" }],
};

type ReportPoint = {
  id: string;
  lat: number;
  lng: number;
  severity: number;
  debris_type: string | null;
};

type CleanupRow = {
  id: string;
  geom_wkt: string;
  kg_collected: number;
};

function parsePolygonWKT(wkt: string): number[][] | null {
  // POLYGON((lon lat, lon lat, ...))
  const m = wkt.match(/POLYGON\s*\(\((.+)\)\)/i);
  if (!m) return null;
  return m[1].split(",").map((pair) => {
    const [lng, lat] = pair.trim().split(/\s+/).map(Number);
    return [lng, lat];
  });
}

async function fetchReports(bbox: [number, number, number, number]): Promise<ReportPoint[]> {
  try {
    const res = await fetch(`${API}/reports?bbox=${bbox.join(",")}`);
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

async function fetchCleanups(): Promise<CleanupRow[]> {
  try {
    const res = await fetch(`${API}/cleanups?limit=200`);
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

type Mode = "concentration" | "exceedance";

type ForecastMapProps = {
  day: number;
  mode?: Mode;
  quantile?: number;
};

export default function ForecastMap({ day, mode = "concentration", quantile = 0.9 }: ForecastMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const maptilerKey = process.env.NEXT_PUBLIC_MAPTILER_KEY;
    const style = maptilerKey
      ? `https://api.maptiler.com/maps/ocean/style.json?key=${maptilerKey}`
      : (FALLBACK_STYLE as unknown as maplibregl.StyleSpecification);

    const map = new maplibregl.Map({
      container: containerRef.current,
      style,
      center: BLACK_SEA_CENTER,
      zoom: BLACK_SEA_ZOOM,
      maxBounds: [
        [BLACK_SEA_BBOX[0] - 3, BLACK_SEA_BBOX[1] - 1.5],
        [BLACK_SEA_BBOX[2] + 3, BLACK_SEA_BBOX[3] + 1.5],
      ],
    });
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), "bottom-right");
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const layerId = "forecast-tiles";
    const sourceId = "forecast-src";
    const exceedanceSourceId = "exceedance-src";
    const exceedanceLayerId = "exceedance-circles";

    const setupConcentrationLayer = () => {
      if (map.getLayer(exceedanceLayerId)) map.removeLayer(exceedanceLayerId);
      if (map.getSource(exceedanceSourceId)) map.removeSource(exceedanceSourceId);
      if (map.getLayer(layerId)) map.removeLayer(layerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
      const bboxParam = BLACK_SEA_BBOX.join(",");
      map.addSource(sourceId, {
        type: "raster",
        tiles: [
          `${API}/tiles/{z}/{x}/{y}.png?day=${day}&bbox=${bboxParam}`,
        ],
        tileSize: 256,
        bounds: BLACK_SEA_BBOX,
      });
      map.addLayer({
        id: layerId,
        type: "raster",
        source: sourceId,
        paint: { "raster-opacity": 0.65 },
      });
    };

    const setRasterTiles = (newDay: number) => {
      // Public mutator for jurors / playwright — swaps the raster source's
      // tile URL in place without recreating the map.
      const src = map.getSource(sourceId) as maplibregl.RasterTileSource | undefined;
      if (!src) return;
      const bboxParam = BLACK_SEA_BBOX.join(",");
      src.setTiles([`${API}/tiles/{z}/{x}/{y}.png?day=${newDay}&bbox=${bboxParam}`]);
    };
    // Stash on the map so e2e tests can grab it.
    (map as unknown as { __setRasterTiles?: (d: number) => void }).__setRasterTiles = setRasterTiles;

    const setupExceedanceLayer = async () => {
      if (map.getLayer(layerId)) map.removeLayer(layerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
      const bbox: [number, number, number, number] = BLACK_SEA_BBOX;
      try {
        const response = await fetchExceedance(bbox, day + 1, quantile);
        const geojson = {
          type: "FeatureCollection" as const,
          features: response.cells.map((cell) => ({
            type: "Feature" as const,
            properties: { probability: cell.probability },
            geometry: { type: "Point" as const, coordinates: [cell.lng, cell.lat] },
          })),
        };
        if (map.getLayer(exceedanceLayerId)) map.removeLayer(exceedanceLayerId);
        if (map.getSource(exceedanceSourceId)) map.removeSource(exceedanceSourceId);
        map.addSource(exceedanceSourceId, { type: "geojson", data: geojson });
        map.addLayer({
          id: exceedanceLayerId,
          type: "circle",
          source: exceedanceSourceId,
          paint: {
            "circle-radius": [
              "interpolate",
              ["linear"],
              ["zoom"],
              4,
              8,
              10,
              22,
            ],
            "circle-color": [
              "interpolate",
              ["linear"],
              ["get", "probability"],
              0.0,
              "#e5e7eb",
              0.25,
              "#fde68a",
              0.5,
              "#fbbf24",
              0.75,
              "#ef4444",
              1.0,
              "#7f1d1d",
            ],
            "circle-opacity": 0.7,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 0.5,
          },
        });
      } catch (err) {
        // Network failure shouldn't break the demo — silently keep the
        // concentration layer up.
        console.warn("exceedance fetch failed", err);
        setupConcentrationLayer();
      }
    };

    let cancelled = false;
    const run = () => {
      if (cancelled) return;
      if (mode === "concentration") setupConcentrationLayer();
      else void setupExceedanceLayer();
    };

    if (map.isStyleLoaded()) {
      run();
    } else {
      map.once("load", run);
    }

    return () => {
      cancelled = true;
      // Off any "load" listener we attached in case the effect re-fires
      // before the map finished loading the style.
      map.off("load", run);
      // Drop layers/sources for the previous (mode, day) so a switch
      // doesn't leak them.  We're explicit per layer/source so a hot
      // reload doesn't blow up if the map is already partly torn down.
      try {
        if (map.getLayer(exceedanceLayerId)) map.removeLayer(exceedanceLayerId);
        if (map.getSource(exceedanceSourceId)) map.removeSource(exceedanceSourceId);
        if (map.getLayer(layerId)) map.removeLayer(layerId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
      } catch {
        /* map was torn down concurrently — nothing to clean up */
      }
    };
  }, [day, mode, quantile]);

  // Citizen-report points + cleanup polygons (loaded once after style ready).
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const setupCommunityLayers = async () => {
      // Use the Black Sea bbox instead of the whole world — the API
      // rejects bboxes larger than 90°x60° (CRIT-API-14).
      const bbox: [number, number, number, number] = BLACK_SEA_BBOX;
      const [reports, cleanups] = await Promise.all([fetchReports(bbox), fetchCleanups()]);

      const reportsGeoJSON = {
        type: "FeatureCollection" as const,
        features: reports.map((r) => ({
          type: "Feature" as const,
          properties: { severity: r.severity, debris_type: r.debris_type ?? "", id: r.id },
          geometry: { type: "Point" as const, coordinates: [r.lng, r.lat] },
        })),
      };

      const cleanupsGeoJSON = {
        type: "FeatureCollection" as const,
        features: cleanups
          .map((c) => {
            const coords = parsePolygonWKT(c.geom_wkt);
            if (!coords) return null;
            return {
              type: "Feature" as const,
              properties: { kg: c.kg_collected, id: c.id },
              geometry: { type: "Polygon" as const, coordinates: [coords] },
            };
          })
          .filter((f): f is NonNullable<typeof f> => Boolean(f)),
      };

      if (map.getLayer("reports-circles")) map.removeLayer("reports-circles");
      if (map.getSource("reports-src")) map.removeSource("reports-src");
      map.addSource("reports-src", { type: "geojson", data: reportsGeoJSON });
      map.addLayer({
        id: "reports-circles",
        type: "circle",
        source: "reports-src",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["get", "severity"], 1, 4, 5, 11],
          "circle-color": "#0d9488",
          "circle-stroke-color": "#fff",
          "circle-stroke-width": 1.5,
          "circle-opacity": 0.9,
        },
      });

      if (map.getLayer("cleanups-fill")) map.removeLayer("cleanups-fill");
      if (map.getLayer("cleanups-line")) map.removeLayer("cleanups-line");
      if (map.getSource("cleanups-src")) map.removeSource("cleanups-src");
      map.addSource("cleanups-src", { type: "geojson", data: cleanupsGeoJSON });
      map.addLayer({
        id: "cleanups-fill",
        type: "fill",
        source: "cleanups-src",
        paint: { "fill-color": "#fbbf24", "fill-opacity": 0.25 },
      });
      map.addLayer({
        id: "cleanups-line",
        type: "line",
        source: "cleanups-src",
        paint: { "line-color": "#f59e0b", "line-width": 2 },
      });

      const onReportClick = (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
        const f = e.features?.[0];
        if (!f || f.geometry.type !== "Point") return;
        new maplibregl.Popup()
          .setLngLat(f.geometry.coordinates as [number, number])
          .setHTML(
            `<strong>${f.properties?.debris_type ?? "report"}</strong><br />severity ${f.properties?.severity ?? "?"}`,
          )
          .addTo(map);
      };
      map.on("click", "reports-circles", onReportClick);
      clickHandlers.push(onReportClick);
    };

    const clickHandlers: Array<
      (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => void
    > = [];

    const onLoad = () => void setupCommunityLayers();
    if (map.isStyleLoaded()) {
      void setupCommunityLayers();
    } else {
      map.once("load", onLoad);
    }

    return () => {
      map.off("load", onLoad);
      for (const h of clickHandlers) {
        try {
          map.off("click", "reports-circles", h);
        } catch {
          /* layer already removed */
        }
      }
      try {
        if (map.getLayer("reports-circles")) map.removeLayer("reports-circles");
        if (map.getSource("reports-src")) map.removeSource("reports-src");
        if (map.getLayer("cleanups-fill")) map.removeLayer("cleanups-fill");
        if (map.getLayer("cleanups-line")) map.removeLayer("cleanups-line");
        if (map.getSource("cleanups-src")) map.removeSource("cleanups-src");
      } catch {
        /* map torn down */
      }
    };
  }, []);

  return <div ref={containerRef} className="w-full h-[calc(100vh-64px)]" aria-label="Forecast map" />;
}
