"""Pydantic schemas for forecast responses."""

from __future__ import annotations

from pydantic import BaseModel


class ForecastCell(BaseModel):
    lat: float
    lng: float
    concentration: float


class ForecastDay(BaseModel):
    day: int  # D+0, D+1, ...
    cells: list[ForecastCell]


class ForecastResponse(BaseModel):
    model_version: str
    bbox: list[float]  # [lon_min, lat_min, lon_max, lat_max]
    horizon_days: int
    days: list[ForecastDay]
    as_of_date: str | None = None
    ground_truth_available: bool = False
    skill_score_vs_actual: dict[str, float] | None = None


class ExceedanceCell(BaseModel):
    lat: float
    lng: float
    probability: float  # 0..1


class ExceedanceResponse(BaseModel):
    model_version: str
    bbox: list[float]
    horizon_days: int
    threshold: float  # concentration units (same as ForecastResponse)
    quantile: float  # quantile used to derive threshold when caller did not pass one
    n_members: int
    cells: list[ExceedanceCell]


# ----------------------------------------------------------------------------
# /forecast/explain — SHAP-style physical decomposition (code feature #1)
# ----------------------------------------------------------------------------


class ForecastDecomposition(BaseModel):
    advection_u_ocean: float
    advection_v_ocean: float
    windage_u_wind: float
    windage_v_wind: float
    diffusion: float
    beaching: float
    biofouling: float
    stokes_drift: float


class PhysicsParams(BaseModel):
    alpha_learned: float
    K_learned: float
    lambda_learned: float
    stokes_beta_learned: float | None = None


class ExplainResponse(BaseModel):
    lat: float
    lng: float
    horizon_days: int
    as_of_date: str | None = None
    prediction: float
    ci_95: tuple[float, float]
    decomposition: ForecastDecomposition
    physics_params: PhysicsParams
    ensemble_disagreement: float
    model_version: str


# ----------------------------------------------------------------------------
# /forecast/backward — reverse-trajectory source attribution (stretch #6)
# ----------------------------------------------------------------------------


class BackwardSourceCell(BaseModel):
    lat: float
    lng: float
    probability: float


class BackwardResponse(BaseModel):
    model_version: str
    target: tuple[float, float]  # (lat, lng)
    days_back: int
    method: str  # "lagrangian-backward" / "pinn-time-reverse"
    cells: list[BackwardSourceCell]
    top_sources: list[dict]  # {"name": "Danube delta", "probability": 0.37}


# ----------------------------------------------------------------------------
# /forecast/counterfactual — physics-knob ablation (code feature #11)
# ----------------------------------------------------------------------------


class CounterfactualResponse(BaseModel):
    base: ForecastResponse
    modified: ForecastResponse
    modifications: dict[str, float]
    delta_mean: float
    delta_max: float


# ----------------------------------------------------------------------------
# /forecast/active_learning — BALD acquisition over the 5-seed ensemble
# (stretch #9)
# ----------------------------------------------------------------------------


class ActiveLearningPoint(BaseModel):
    lat: float
    lng: float
    bald_score: float
    suggested_action: str  # "deploy_drifter" / "send_volunteer" / "request_photo"


class ActiveLearningResponse(BaseModel):
    bbox: list[float]
    horizon_days: int
    top_points: list[ActiveLearningPoint]
    rationale: str
    model_version: str
