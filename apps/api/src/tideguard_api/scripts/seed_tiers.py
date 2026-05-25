"""Seed/refresh the ``tiers`` table from the static :mod:`feature_gate` table."""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from tideguard_api.db import SessionLocal
from tideguard_api.models.tier import Tier
from tideguard_api.services.feature_gate import TIERS


async def main() -> None:
    async with SessionLocal() as db:
        for slug, t in TIERS.items():
            res = await db.execute(select(Tier).where(Tier.slug == slug))
            row = res.scalar_one_or_none()
            if row is None:
                row = Tier(
                    id=uuid.uuid4(),
                    slug=slug,
                    category=t.get("category", "api"),
                    display_name=t.get("display_name", slug),
                    price_monthly_usd=float(t.get("price_monthly_usd", 0.0)),
                    price_yearly_usd=float(t.get("price_monthly_usd", 0.0)) * 10,
                    features=t,
                    active=True,
                )
                db.add(row)
                print(f"[seed_tiers] inserted {slug}")
            else:
                row.display_name = t.get("display_name", slug)
                row.category = t.get("category", "api")
                row.price_monthly_usd = float(t.get("price_monthly_usd", 0.0))
                row.price_yearly_usd = float(t.get("price_monthly_usd", 0.0)) * 10
                row.features = t
                row.active = True
                print(f"[seed_tiers] updated  {slug}")
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
