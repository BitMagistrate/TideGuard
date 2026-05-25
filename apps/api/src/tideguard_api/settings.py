"""Application settings loaded from environment variables.

Hardened per TASK-005 (TIDEGUARD_AUDIT.md):
  * `env` selects "development" | "staging" | "production".
  * `get_settings()` raises a `RuntimeError` at import time if production is
    misconfigured (default JWT, anonymous fallback, missing storage, sqlite).
  * `validate_for_environment()` exposed for tests / startup hooks.
"""

from __future__ import annotations

import re
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRETS = {
    "",
    "dev-secret-change-me",
    "change-me",
    "secret",
}


class Settings(BaseSettings):
    """Centralised configuration for the API service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"  # production | staging | development | test
    database_url: str = "sqlite+aiosqlite:///./tideguard_dev.db"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://tideguard.app",
        "https://www.tideguard.app",
    ]
    # Comma-separated list of extra CORS origins (full URLs, no trailing slash).
    # Set via env var ``EXTRA_CORS_ORIGINS`` on Fly.io / Render etc. to whitelist
    # whatever URL Vercel actually assigned to the frontend deploy.
    # Example: ``EXTRA_CORS_ORIGINS=https://mnohyjmg.vercel.app,https://my-other.netlify.app``
    extra_cors_origins: str = ""
    # When true the API runs all idempotent seeders (regions, beach segments,
    # education tiers) inside the FastAPI lifespan hook on startup. Useful for
    # one-click hobby deployments (Fly.io, Render) where there is no separate
    # migrate-and-seed step. Defaults to false so we don't surprise prod ops.
    auto_seed_on_startup: bool = False
    # Regex-based origins that authorise preview / hobby deployments.
    # Defaults are permissive on purpose so a freshly-deployed Vercel/Netlify/
    # Fly app talks to the API without manual CORS configuration. Tighten this
    # in production by setting ``CORS_ORIGIN_REGEX`` to a stricter pattern.
    cors_origin_regex: str = (
        r"^https://([a-z0-9-]+\.)*"
        r"(vercel\.app|netlify\.app|pages\.dev|fly\.dev|onrender\.com|"
        r"tideguard\.app)$"
    )

    # Auth — HS256 JWT
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "tideguard"
    jwt_audience: str = "tideguard-app"
    jwt_kid: str = "tideguard-v1"
    jwt_ttl_seconds: int = 60 * 60 * 24 * 7  # one week
    allow_anonymous_dev_user: bool = True

    # P1-14 — OIDC federation (e.g. Google / Microsoft / Yandex).
    oidc_issuer: str = ""
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_redirect_uri: str = "https://api.tideguard.app/auth/oidc/callback"

    # Supabase (optional)
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # Object storage
    s3_endpoint: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket_data: str = "tideguard-data"
    s3_bucket_photos: str = "tideguard-photos"

    # ML
    pinn_checkpoint_path: str = "checkpoints/pinn_demo.pt"
    pinn_ensemble_dir: str = ""
    forcing_zarr_path: str = ""  # e.g. s3://tideguard-data/forcing.zarr
    # Defines the geographic domain assumed by the loaded checkpoint.
    # Defaults to the Black Sea pilot zone.
    domain_lon_min: float = 27.0
    domain_lon_max: float = 42.0
    domain_lat_min: float = 40.0
    domain_lat_max: float = 47.0
    domain_name: str = "black_sea"

    # Photo upload guardrails
    photo_max_bytes: int = 10 * 1024 * 1024
    photo_allowed_mime: tuple[str, ...] = (
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/heic",
    )
    # Hard ASGI body limit (a bit larger than photo_max_bytes to allow form overhead).
    request_max_body_bytes: int = 12 * 1024 * 1024
    # ClamAV sidecar (optional). Unix socket path.
    clamav_socket: str = ""
    # Perceptual-hash duplicate threshold (Hamming distance).
    photo_phash_max_distance: int = 6
    # EXIF GPS cross-check tolerance (metres).
    photo_gps_tolerance_meters: float = 200.0

    # Rate limiting
    rate_limit_per_minute: int = 60
    # Trusted proxy chain — when present in headers we use the upstream IP
    # for slowapi rate-limit keying instead of `127.0.0.1`.
    trusted_proxy_headers: tuple[str, ...] = (
        "fly-client-ip",
        "cf-connecting-ip",
        "x-real-ip",
        "x-forwarded-for",
    )

    # Caching
    forecast_cache_ttl_seconds: int = 3600

    # Observability
    sentry_dsn: str = ""
    log_level: str = "INFO"
    log_json: bool = False
    metrics_enabled: bool = True

    # Education / certification
    certification_min_lessons: int = 5
    certification_min_score: float = 0.7
    certification_per_lesson_cooldown_seconds: int = 24 * 3600

    # -- v0.5 monetisation block --
    # Billing
    billing_provider: str = "stripe"        # stripe | paddle | manual
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_publishable_key: str = ""
    paddle_vendor_id: str = ""
    paddle_api_key: str = ""
    paddle_public_key: str = ""
    # Email
    email_provider: str = "resend"          # resend | postmark | ses | console
    resend_api_key: str = ""
    postmark_server_token: str = ""
    email_from: str = "TideGuard <noreply@tideguard.app>"
    magic_link_ttl_seconds: int = 15 * 60
    # SMS
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    # Telegram
    telegram_bot_token: str = ""
    # VRP / routing
    osrm_base_url: str = "https://routing.openstreetmap.de"
    or_tools_solver_time_limit_ms: int = 10_000
    # API-key / tier enforcement
    api_key_enforcement: bool = False       # if True, every endpoint goes through the gate
    api_key_redis_namespace: str = "tg:usage"
    # ESG
    esg_risk_grid_cell_deg: float = 0.05
    esg_methodology_version: str = "esg-v1.0"
    # Adopt-a-beach
    adopt_segment_default_length_m: float = 1000.0
    adopt_max_active_per_user: int = 5

    def validate_for_environment(self) -> list[str]:
        """Return a list of problems if the configuration is unsafe for prod."""
        problems: list[str] = []
        if self.env != "production":
            return problems
        if self.jwt_secret.strip().lower() in DEFAULT_JWT_SECRETS:
            problems.append("JWT_SECRET must be set to a strong value in production")
        if len(self.jwt_secret) < 32:
            problems.append("JWT_SECRET must be >= 32 characters in production")
        if self.allow_anonymous_dev_user:
            problems.append("ALLOW_ANONYMOUS_DEV_USER must be false in production")
        if self.database_url.startswith("sqlite"):
            problems.append("DATABASE_URL must be PostgreSQL in production")
        if not self.s3_endpoint:
            problems.append("S3_ENDPOINT must be configured in production (no local fs fallback)")
        if "*" in self.cors_origins:
            problems.append("CORS_ORIGINS must not contain '*' in production")
        if self.cors_origin_regex:
            try:
                re.compile(self.cors_origin_regex)
            except re.error as exc:
                problems.append(f"CORS_ORIGIN_REGEX is not valid regex: {exc}")
        # v0.5 — billing checks (only enforced when api_key_enforcement is enabled in prod)
        if self.api_key_enforcement:
            if self.billing_provider not in ("stripe", "paddle", "manual"):
                problems.append("BILLING_PROVIDER must be one of stripe|paddle|manual")
            if self.billing_provider == "stripe" and not self.stripe_webhook_secret:
                problems.append("STRIPE_WEBHOOK_SECRET must be set in production when stripe is active")
            if self.billing_provider == "paddle" and not self.paddle_public_key:
                problems.append("PADDLE_PUBLIC_KEY must be set in production when paddle is active")
        return problems


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    problems = s.validate_for_environment()
    if problems:
        raise RuntimeError("Insecure production config: " + "; ".join(problems))
    return s
