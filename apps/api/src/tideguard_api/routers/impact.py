"""Public Impact API (P1-12).

This router complements the cumulative-summary endpoint in
``b2g.py /impact`` with a causal-effect estimate based on a synthetic
control: we model the cleanups time-series in a treated region by a
weighted combination of donor regions trained on the pre-intervention
window, and report the gap on the post-intervention window as the
causal impact.

The endpoint accepts the time-series via query params for ease of
demo (and so the front-end can wire it directly into a chart); a
production deployment would pull the series from the operational
database instead.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from tideguard_api.services.causal_impact import causal_impact

router = APIRouter(prefix="/impact", tags=["impact"])


def _parse_csv_floats(s: str) -> list[float]:
    try:
        return [float(x.strip()) for x in s.split(",") if x.strip()]
    except ValueError as exc:
        raise HTTPException(400, f"bad CSV: {exc}") from exc


@router.get("/causal")
def causal_endpoint(
    treated: str = Query(..., description="Comma-separated treated-series values"),
    donors: str = Query(..., description="Semicolon-separated donor series, each comma-separated"),
    intervention_index: int = Query(..., ge=1),
) -> dict:
    """Synthetic-control causal-impact estimate.

    Example::

        GET /impact/causal
            ?treated=1,2,3,4,8,9,10
            &donors=1,2,3,4,4,5,6;0,1,2,3,3,4,5
            &intervention_index=4

    Returns ``counterfactual``, ``impact``, ``cumulative_impact``,
    ``relative_effect`` (fraction), ``donor_weights`` (simplex), and
    the pre-intervention ``pre_rmse`` (a fit quality metric).
    """
    treated_values = _parse_csv_floats(treated)
    donor_lists = [_parse_csv_floats(s) for s in donors.split(";") if s.strip()]
    if not donor_lists:
        raise HTTPException(400, "at least one donor series required")
    if any(len(d) != len(treated_values) for d in donor_lists):
        raise HTTPException(400, "every donor must match treated length")
    result = causal_impact(
        treated=treated_values,
        donors=donor_lists,
        intervention_index=intervention_index,
    )
    return result.to_dict() | {
        "n_donors": len(donor_lists),
        "intervention_index": intervention_index,
    }
