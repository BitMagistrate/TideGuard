# TideGuard AI

**AI that predicts plastic before it pollutes.**

TideGuard AI is an open-source citizen-science platform that combines a
Physics-Informed Neural Network with a community action layer to forecast,
report and prevent floating marine debris.

[![Code](https://img.shields.io/badge/Code-MIT-22c55e.svg)](LICENSE)
[![Content](https://img.shields.io/badge/Content-CC--BY--4.0-22c55e.svg)](content/)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-22c55e.svg)](CONTRIBUTING.md)
[![Version](https://img.shields.io/badge/release-v0.5.7-22c55e.svg)](CHANGELOG.md)

- **Physics-Informed Neural Network** (PyTorch) — trained on the 2D
  advection-diffusion equation, **learns** windage `α`, diffusion `K` and
  beaching rate `λ` from data. Includes a 5-seed deep ensemble for
  uncertainty quantification. Persistence and Lagrangian baselines for
  honest benchmarking.
- **FastAPI** backend with HS256 JWT auth, slowapi rate limiting,
  structured logs, Sentry hook, EXIF-stripping photo uploads,
  PostGIS-ready geometries, Alembic migrations, badges service,
  moderator queue.
- **Next.js 14** web dashboard with MapLibre, live forecast/report/cleanup
  layers, an *honest* KPI section (`/cleanups/stats`), a moderator queue,
  and a `/method` page that explains the maths to non-technical jurors.
- **Flutter 3** mobile app with real photo+GPS report submission,
  `flutter_map` view of the forecast, offline lessons and a quiz screen.
- **Environmental Education module** — 10 markdown lessons + quizzes +
  SDG metadata + practical task + teacher guide + PDF certificate.

## Repository layout

```
tideguard/
├── apps/
│   ├── ml/          # PyTorch PINN, training, ingest, baselines, ensemble
│   ├── api/         # FastAPI + SQLAlchemy + Alembic + (PostGIS)
│   ├── web/         # Next.js 14 + MapLibre + Tailwind
│   └── mobile/      # Flutter 3 + Riverpod + go_router + flutter_map
├── content/lessons/ # 10 markdown lessons with embedded JSON quizzes
├── infra/           # Docker + docker-compose + fly.toml
├── packages/        # shared schemas / cross-app code
├── scripts/         # research, validation and ops utilities
└── .github/workflows/  # CI for each app
```

## Quickstart

### 0. One-shot setup

```bash
make setup     # installs uv envs, pnpm install, flutter pub get
make demo      # trains a tiny PINN, seeds lessons, starts API + web
```

### 1. Backend (API)

```bash
cd apps/api
uv venv && uv pip install -e ".[dev]"
uv run pytest -q                       # all tests pass
uv run uvicorn tideguard_api.main:app --reload
# visit http://localhost:8000/docs
```

Seed the EE lessons:
```bash
curl -X POST http://localhost:8000/education/_seed
```

### 2. ML — train the PINN

```bash
cd apps/ml
uv venv && uv pip install -e ".[dev]"
uv run pytest -q
# Synthetic
uv run python -m tideguard_ml.train --synthetic --epochs 2000
# Real (requires data/real/observations.csv)
uv run python -m tideguard_ml.train --real --csv data/real/observations.csv --epochs 2000
# Honest benchmark vs persistence + Lagrangian
uv run python -m tideguard_ml.baselines.benchmark --seeds 5
```

### 3. Web

```bash
pnpm install
pnpm --filter @tideguard/web dev
# visit http://localhost:3000
```

### 4. Mobile

```bash
cd apps/mobile
flutter pub get
flutter run
```

### 5. All-in-one via Docker

```bash
cd infra
docker compose -f docker-compose.dev.yml up --build
```

## The science

TideGuard's PINN solves the 2D advection-diffusion equation for surface debris concentration:

```
∂C/∂t + ∇·((u_ocean + α·u_wind) · C) − ∇·(K · ∇C) + λ · C = S(x,y,t)
```

with three **learnable physical parameters**:

- **α** — windage coefficient (≈ 0.03 for bottles; the model fine-tunes per debris type)
- **K** — diffusion coefficient (m²/s)
- **λ** — beaching rate (1/day)

## Endpoints (selected)

| Method | Path                          | Purpose                              |
|-------:|-------------------------------|--------------------------------------|
| GET    | `/healthz`                    | Health check                         |
| GET    | `/me`                         | Current user profile                 |
| POST   | `/auth/dev_token`             | Issue a dev JWT (HS256) for testing  |
| GET    | `/forecast`                   | Predicted concentration grid (`?as_of_date=` enables time-machine) |
| GET    | `/forecast/explain`           | Physics-decomposed SHAP-like explanation (v0.4) |
| GET    | `/forecast/backward`          | Reverse-trajectory source attribution (v0.4) |
| GET    | `/forecast/counterfactual`    | "What-if" scenarios on wind / current / windage (v0.4) |
| GET    | `/forecast/active_learning`   | BALD-ranked points for citizen observers (v0.4) |
| GET    | `/forecast/exceedance`        | Per-pixel probability-of-exceedance map |
| GET    | `/cleanup_planner`            | Weather + wave + tide ranked cleanup days (v0.4) |
| GET    | `/sustainability/footprint`   | Project carbon ledger (CodeCarbon-backed, v0.4) |
| GET    | `/ogc/wms`                    | OGC WMS 1.3.0 GetCapabilities + GetMap (v0.4) |
| GET    | `/ogc/stac/catalog.json`      | STAC 1.0.0 catalog of daily forecasts (v0.4) |
| GET    | `/ogc/geojson`                | GeoJSON export of the final-day grid (v0.4) |
| GET    | `/developers`                 | Machine-readable public API docs (v0.4) |
| GET    | `/tiles/{z}/{x}/{y}.png`      | Raster heatmap tile (from PINN)      |
| POST   | `/reports`                    | Submit a citizen report (photo+GPS)  |
| GET    | `/reports`                    | List approved reports in bbox        |
| GET    | `/reports/queue`              | Moderator queue (pending reports)    |
| PATCH  | `/reports/{id}`               | Moderator: approve/reject (JSON body)|
| GET    | `/reports/mine`               | Reports submitted by the caller      |
| DELETE | `/reports/mine`               | GDPR Art. 17 right-to-erasure        |
| POST   | `/cleanups`                   | Log a cleanup event (polygon + kg)   |
| GET    | `/cleanups/stats`             | Aggregate KPIs (public)              |
| GET    | `/education/lessons`          | List EE lessons                      |
| GET    | `/education/lessons/{slug}`   | Lesson body + quiz                   |
| POST   | `/education/progress`         | Record quiz progress, award XP       |
| GET    | `/education/certificate`      | Generate PDF certificate (≥5 done)   |
| GET    | `/leaderboard?scope=school&school_id=…` | Top users by XP             |
| GET    | `/badges/mine`                | Badges awarded to the caller         |
| GET    | `/admin/kpi`                  | Impact dashboard (admin only)        |

## License

- Code: MIT (see [LICENSE](LICENSE))
- Lesson content: CC-BY-4.0

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
Security reports: [SECURITY.md](SECURITY.md).

## Acknowledgements

PINN methodology inspired by Raissi et al. (2019) and Biermann et al. (2020).
Ocean current data: Copernicus Marine Service (CMEMS). Wind reanalysis: ECMWF ERA5.
Black Sea regional sources: Copernicus Marine Service NEMO regional model, NOAA OSCAR.

## Author

**Vladimir Aleksandrovich Yermolenko**, 17, Krasnoyarsk, Russia.
Founder and lead developer of TideGuard AI, built with an AI coding co-pilot.
Contact: [scaleblinkk@vk.com](mailto:scaleblinkk@vk.com)

## Автор

**Ермоленко Владимир Александрович**, 17 лет, Красноярск, Россия.
Создатель и ведущий разработчик TideGuard AI, проект разработан в паре с AI-копайлотом.
Связь: [scaleblinkk@vk.com](mailto:scaleblinkk@vk.com)
