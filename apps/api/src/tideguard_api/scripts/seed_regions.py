"""Seed the ``regions`` table with the priority RU + INT cities listed in §4."""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from tideguard_api.db import SessionLocal
from tideguard_api.models.region import Region

REGIONS = [
    # 7 RU coastal cities (Black Sea + Caspian)
    {"slug": "anapa", "ru": "Анапа", "en": "Anapa", "country": "RU",
     "bbox": [37.20, 44.79, 37.55, 44.99], "beach_length_km": 60.0, "population": 80000},
    {"slug": "gelendzhik", "ru": "Геленджик", "en": "Gelendzhik", "country": "RU",
     "bbox": [37.85, 44.50, 38.30, 44.71], "beach_length_km": 30.0, "population": 70000},
    {"slug": "sochi", "ru": "Сочи", "en": "Sochi", "country": "RU",
     "bbox": [39.50, 43.30, 40.20, 43.80], "beach_length_km": 145.0, "population": 460000},
    {"slug": "novorossiysk", "ru": "Новороссийск", "en": "Novorossiysk", "country": "RU",
     "bbox": [37.55, 44.65, 37.85, 44.80], "beach_length_km": 20.0, "population": 270000},
    {"slug": "tuapse", "ru": "Туапсе", "en": "Tuapse", "country": "RU",
     "bbox": [39.00, 44.05, 39.20, 44.15], "beach_length_km": 15.0, "population": 64000},
    {"slug": "makhachkala", "ru": "Махачкала", "en": "Makhachkala", "country": "RU",
     "bbox": [47.30, 42.92, 47.65, 43.15], "beach_length_km": 24.0, "population": 605000},
    {"slug": "derbent", "ru": "Дербент", "en": "Derbent", "country": "RU",
     "bbox": [48.25, 41.95, 48.40, 42.15], "beach_length_km": 12.0, "population": 125000},
    # 15 international coastal cities
    {"slug": "miami_fl", "ru": "Майами", "en": "Miami", "country": "US",
     "bbox": [-80.30, 25.55, -80.05, 25.85], "beach_length_km": 19.0, "population": 470000},
    {"slug": "los_angeles", "ru": "Лос-Анджелес", "en": "Los Angeles", "country": "US",
     "bbox": [-118.55, 33.70, -118.20, 34.05], "beach_length_km": 120.0, "population": 3900000},
    {"slug": "rio_de_janeiro", "ru": "Рио-де-Жанейро", "en": "Rio de Janeiro", "country": "BR",
     "bbox": [-43.40, -23.05, -43.10, -22.80], "beach_length_km": 90.0, "population": 6700000},
    {"slug": "sydney", "ru": "Сидней", "en": "Sydney", "country": "AU",
     "bbox": [151.10, -33.95, 151.35, -33.75], "beach_length_km": 75.0, "population": 5300000},
    {"slug": "barcelona", "ru": "Барселона", "en": "Barcelona", "country": "ES",
     "bbox": [2.10, 41.30, 2.30, 41.45], "beach_length_km": 9.0, "population": 1620000},
    {"slug": "nice", "ru": "Ницца", "en": "Nice", "country": "FR",
     "bbox": [7.20, 43.65, 7.35, 43.75], "beach_length_km": 8.0, "population": 340000},
    {"slug": "antalya", "ru": "Анталья", "en": "Antalya", "country": "TR",
     "bbox": [30.65, 36.80, 30.95, 36.95], "beach_length_km": 65.0, "population": 2500000},
    {"slug": "phuket", "ru": "Пхукет", "en": "Phuket", "country": "TH",
     "bbox": [98.25, 7.80, 98.45, 8.15], "beach_length_km": 30.0, "population": 80000},
    {"slug": "bali", "ru": "Бали", "en": "Bali (Denpasar)", "country": "ID",
     "bbox": [115.10, -8.85, 115.30, -8.50], "beach_length_km": 80.0, "population": 1700000},
    {"slug": "goa", "ru": "Гоа", "en": "Goa", "country": "IN",
     "bbox": [73.80, 15.20, 74.05, 15.65], "beach_length_km": 100.0, "population": 200000},
    {"slug": "cancun", "ru": "Канкун", "en": "Cancun", "country": "MX",
     "bbox": [-86.95, 21.05, -86.75, 21.25], "beach_length_km": 23.0, "population": 700000},
    {"slug": "santorini", "ru": "Санторини", "en": "Santorini", "country": "GR",
     "bbox": [25.30, 36.30, 25.55, 36.55], "beach_length_km": 4.0, "population": 15000},
    {"slug": "lagos_pt", "ru": "Лагуш", "en": "Lagos", "country": "PT",
     "bbox": [-8.75, 37.05, -8.55, 37.20], "beach_length_km": 8.0, "population": 31000},
    {"slug": "okinawa", "ru": "Окинава", "en": "Okinawa (Naha)", "country": "JP",
     "bbox": [127.60, 26.10, 127.85, 26.30], "beach_length_km": 12.0, "population": 320000},
    {"slug": "cape_town", "ru": "Кейптаун", "en": "Cape Town", "country": "ZA",
     "bbox": [18.30, -34.20, 18.55, -33.85], "beach_length_km": 35.0, "population": 4600000},
]


async def main() -> None:
    async with SessionLocal() as db:
        for r in REGIONS:
            res = await db.execute(select(Region).where(Region.slug == r["slug"]))
            row = res.scalar_one_or_none()
            if row is None:
                db.add(
                    Region(
                        id=uuid.uuid4(),
                        slug=r["slug"],
                        display_name_ru=r["ru"],
                        display_name_en=r["en"],
                        country=r["country"],
                        bbox=r["bbox"],
                        beach_length_km=r["beach_length_km"],
                        extra={
                            "population": r["population"],
                            "cost_per_kg_eur": 0.62,
                            "methodology_version": "esg-v1.0",
                        },
                    )
                )
                print(f"[seed_regions] inserted {r['slug']}")
            else:
                row.display_name_ru = r["ru"]
                row.display_name_en = r["en"]
                row.country = r["country"]
                row.bbox = r["bbox"]
                row.beach_length_km = r["beach_length_km"]
                print(f"[seed_regions] updated  {r['slug']}")
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
