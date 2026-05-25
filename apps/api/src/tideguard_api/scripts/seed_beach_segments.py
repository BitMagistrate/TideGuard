"""Seed the ``beach_segments`` table by slicing each region's synthetic coastline.

In production this script consumes ``data/coastline.geojson`` produced by
``apps/ml/scripts/build_coastline.py`` (OSM extract). For dev / tests we
fall back to :func:`geometry.synthetic_coast_for_bbox`.
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from tideguard_api.db import SessionLocal
from tideguard_api.models.beach_segment import BeachSegment
from tideguard_api.models.region import Region
from tideguard_api.services.geometry import slice_coastline, synthetic_coast_for_bbox


async def main() -> None:
    async with SessionLocal() as db:
        regions = (await db.execute(select(Region))).scalars().all()
        if not regions:
            print("[seed_beach_segments] no regions found — run seed_regions first")
            return
        for r in regions:
            coords = synthetic_coast_for_bbox(tuple(r.bbox))
            segs = slice_coastline(coords, segment_length_m=1000.0, name_prefix=r.slug)
            for s in segs:
                existing = await db.execute(select(BeachSegment).where(BeachSegment.slug == s.slug))
                if existing.scalar_one_or_none() is not None:
                    continue
                db.add(
                    BeachSegment(
                        id=uuid.uuid4(),
                        slug=s.slug,
                        region_id=r.id,
                        geom_wkt=s.geom_wkt,
                        length_m=s.length_m,
                        midpoint_lat=s.midpoint_lat,
                        midpoint_lng=s.midpoint_lng,
                        display_name=f"{r.display_name_en}: segment {s.slug.split('-')[-1]}",
                        status="available",
                    )
                )
            print(f"[seed_beach_segments] {r.slug}: {len(segs)} segments")
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
