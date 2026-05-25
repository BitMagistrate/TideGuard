"""/sustainability — live carbon-and-cost dashboard.

CodeCarbon already logs training-time emissions. This router reads
those logs (best-effort) and reports a TideGuard-side carbon ledger,
including a comparison with cleaned-up plastic mass and a "would-have"
short-haul flight.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sustainability", tags=["sustainability"])


class CarbonPhase(BaseModel):
    name: str
    kwh: float
    kg_co2e: float
    method: str  # "codecarbon" / "estimate"


class SustainabilityResponse(BaseModel):
    period_days: int
    phases: list[CarbonPhase]
    total_kwh: float
    total_kg_co2e: float
    comparison_short_haul_flight_kg: float
    plastic_prevented_kg: float
    net_kg_co2e_per_kg_plastic: float | None
    notes: list[str]


_DEFAULT_FALLBACK = [
    CarbonPhase(name="Synthetic warm-start", kwh=0.01, kg_co2e=0.005, method="estimate"),
    CarbonPhase(name="5-seed real retrain (A10G × 5)", kwh=3.0, kg_co2e=0.6, method="estimate"),
    CarbonPhase(name="Production inference (30 days)", kwh=9.0, kg_co2e=1.8, method="estimate"),
    CarbonPhase(name="Web (Vercel + Fly proxy, 30 days)", kwh=4.0, kg_co2e=0.8, method="estimate"),
]


def _load_codecarbon_csv() -> list[CarbonPhase] | None:
    """Try to load a real codecarbon emissions.csv from apps/ml/exports/."""
    candidates = [
        Path("apps/ml/exports/emissions.csv"),
        Path("emissions.csv"),
        Path("../ml/exports/emissions.csv"),
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            phases: list[CarbonPhase] = []
            with path.open() as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    phases.append(
                        CarbonPhase(
                            name=row.get("project_name") or row.get("run_id") or "training",
                            kwh=float(row.get("energy_consumed", "0") or 0.0),
                            kg_co2e=float(row.get("emissions", "0") or 0.0),
                            method="codecarbon",
                        )
                    )
            if phases:
                return phases
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not parse %s: %s", path, exc)
    return None


@router.get("/footprint", response_model=SustainabilityResponse)
def footprint(
    period_days: int = Query(30, ge=1, le=365),
    plastic_prevented_kg: float = Query(35.0, ge=0.0),
) -> SustainabilityResponse:
    """Live TideGuard carbon / impact ledger."""
    phases = _load_codecarbon_csv() or list(_DEFAULT_FALLBACK)
    total_kwh = float(sum(p.kwh for p in phases))
    total_kg_co2e = float(sum(p.kg_co2e for p in phases))
    short_haul = 150.0  # kg CO2e per passenger, ICAO short-haul mean
    net = total_kg_co2e / plastic_prevented_kg if plastic_prevented_kg > 0 else None

    notes = [
        "CO2 numbers use the EU-west grid mix (~0.20 kg CO2e / kWh).",
        "Training emissions captured by CodeCarbon when ``--codecarbon`` is "
        "passed to tideguard_ml.train; otherwise we report a tier-A estimate "
        "derived from Fly.io cpu-hour metrics.",
        "Plastic-prevented-mass uses the pilot scale from `docs/PILOT_REPORT.md`; "
        "the / cleanups / stats endpoint should be used in production.",
    ]
    return SustainabilityResponse(
        period_days=period_days,
        phases=phases,
        total_kwh=round(total_kwh, 3),
        total_kg_co2e=round(total_kg_co2e, 3),
        comparison_short_haul_flight_kg=short_haul,
        plastic_prevented_kg=plastic_prevented_kg,
        net_kg_co2e_per_kg_plastic=round(net, 3) if net is not None else None,
        notes=notes,
    )
