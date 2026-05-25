# TideGuard AI — Setup

## Prerequisites

- Node.js **22.x** (tested with v22.12.0)
- pnpm **9.x** (tested with 9.15.1) — `npm i -g pnpm@9`
- Python **3.11**
- `uv` (recommended) or `pip`

## 1) Start the API

```bash
cd apps/api
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
# create a fresh dev SQLite DB and apply all migrations
alembic upgrade head
# seed the demo data (3 tiers, 22 regions, ~540 beach segments, 30 lessons)
python -m src.tideguard_api.seed.tiers
python -m src.tideguard_api.seed.regions
python -m src.tideguard_api.seed.segments
python -m src.tideguard_api.seed.lessons
# start it
uvicorn src.tideguard_api.main:app --host 0.0.0.0 --port 8000
```

Smoke test:

```bash
curl http://localhost:8000/healthz
curl 'http://localhost:8000/forecast?bbox=37.2,44.79,37.55,44.99'
curl 'http://localhost:8000/tiles/5/19/10.png?day=0&bbox=27,40,42,47' -o /tmp/tile.png
```

If any seed script is missing, look in `apps/api/scripts/` — there are
HTTP-based seed endpoints too: `POST /education/_seed`,
`POST /adopt/segments/_seed`.

## 2) Start the Web

```bash
cd apps/web
pnpm install
NEXT_PUBLIC_API_URL=http://localhost:8000 pnpm build
NEXT_PUBLIC_API_URL=http://localhost:8000 pnpm start
# open http://localhost:3000
```

For the prod deploy, set `NEXT_PUBLIC_API_URL` to your Fly.io / Render
URL **before the build**, otherwise the live map will point at
`localhost:8000` and show no heatmap.

## 3) Run tests

```bash
# API
cd apps/api && source .venv/bin/activate && python -m pytest

# Web
cd apps/web && pnpm test
```

## 4) Deploy

- Backend → Fly.io free tier → `https://<app>.fly.dev`
- Frontend → Vercel free tier → `https://<app>.vercel.app`

Make sure CSP in `apps/web/next.config.mjs` includes the value of
`NEXT_PUBLIC_API_URL` at build time so the live map can fetch tiles.
