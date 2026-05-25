# Roadmap

12-month rolling roadmap. Updated quarterly.

## Q1 2026 — submissions sprint (current)

- [x] Bootstrap monorepo, CI per app
- [x] PINN trained on synthetic data with learnable α / K / λ
- [x] FastAPI + web MVP + mobile MVP
- [x] **JWT auth (HS256), no email-as-token, dev `/auth/dev_token` endpoint**
- [x] **EXIF strip + MIME + size limit on photo uploads**
- [x] **slowapi rate limiting, structured logging, Sentry SDK hook**
- [x] **PINN demo checkpoint shipped → tile endpoint serves real model**
- [x] **Live `/cleanups/stats` KPI on landing page (no fabrications)**
- [x] **Moderator queue `/admin/queue`**
- [x] **Persistence + Lagrangian baselines + benchmark script**
- [x] **5-seed deep ensemble for uncertainty quantification**
- [x] **Real founder story + proposal (no `[…]` placeholders)**
- [x] **CONTRIBUTING / CODE_OF_CONDUCT / SECURITY / DATA_ETHICS**
- [x] **Theory of Change + SDG mapping + curriculum mapping**
- [x] **Teacher guide + impact-report template**
- [x] **Mobile: real `POST /reports` + profile from `/me`**
- [x] **Russian-language proposal + founder story («Моя страна — моя Россия»)**
- [x] **3 Russian-language lessons (`content/lessons/ru/`)**
- [x] **Honest benchmark v2 — PINN beats persistence on synthetic D+14**
- [x] **Pitch deck generation prompt + 2:30 video pitch script**
- [x] **Competition submission checklist per prize**
- [ ] Demo screencast (60–90 s) uploaded to YouTube and embedded
- [ ] zh-TW translation of all 10 lessons (one human-review pass)
- [ ] First letter of support secured (school environmental club coordinator)
- [ ] First online pilot (1 school, 5 reporters)
- [ ] Public deploy: API on Fly.io, web on Vercel

## Q2 2026 — first pilot

- [ ] First measured cleanup event (target: 20 kg, 5 students)
- [ ] Quarterly impact report published
- [ ] Forecast skill measured in real environment vs Lagrangian baseline
- [ ] Playwright E2E tests in CI
- [ ] GitHub Actions deploy steps (Vercel + Fly.io)
- [ ] Redis cache layer for forecast results
- [ ] Public preprint of `docs/research_paper.md` on arXiv-equivalent

## Q3 2026 — second region

- [ ] Black Sea regional retrain (CMEMS NEMO regional reanalyses + ERA5)
- [ ] 5 partner schools across 2 countries
- [ ] Full Russian translation of all 10 lessons (10/10)
- [ ] vi + ar translations
- [ ] Optional `TideGuard Pro` enterprise tier scoping
- [ ] WebGPU PINN inference proof-of-concept

## Q4 2026 — sustainability

- [ ] First peer-reviewed paper submitted
- [ ] First in-kind data partnership signed (OpenLitterMap?)
- [ ] First grant beyond initial $2K secured
- [ ] Hardware companion (Pi Zero + camera) prototype

## Beyond

- 20 schools across 4 countries by end of 2027.
- Integration with GEEP regional centre network and Russian Geographic
  Society youth-project programmes.
- Self-hostable Helm chart for institutional deployments.
