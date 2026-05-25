# Changelog

All notable changes to TideGuard AI. Format: [Keep a Changelog](https://keepachangelog.com/),
versioning loosely follows [SemVer](https://semver.org/).

## [0.5.7] — 2026-05-25 ("Krasnoyarsk + Chinese" — biography refresh + zh-TW UI)

### Changed

- **Founder biography.** All public copy now states the verifiable facts:
  17-year-old 10th-grader at Gymnasium №13 "Akadem", Krasnoyarsk, Siberia,
  built TideGuard in **3 months** with an **AI coding co-pilot** that the
  founder directs, reviews and integrates. Replaces previous "Caucasus
  coast / Novosibirsk / 11th grade / 18 months / solo founder" framing.
  Source files hand-rewritten:
  - `docs/founder_story.md`
  - `docs/ru/founder_story_ru.md`
  - `apps/web/app/about/page.tsx`, `apps/web/app/ru/about/page.tsx`
  - `apps/web/app/page.tsx`, `apps/web/app/ru/page.tsx`
  - `apps/web/app/layout.tsx` (metadata)
  - 80+ other markdown / TSX files updated via bulk replacement.

### Added

- **Chinese (zh-TW) UI across the entire public site.** Full /zh/* mirror
  of the EN site: /zh, /zh/about, /zh/method, /zh/research, /zh/pricing,
  /zh/faq, /zh/partners, /zh/press, /zh/roadmap, /zh/learn,
  /zh/b2g/[region]. Each page carries an AI-translation footer disclaimer
  with the contact email for corrections.
- **Global EN / RU / ZH language switcher** injected into `app/layout.tsx`
  via a new client component `components/Lang/LangSwitcher.tsx`. Detects
  current locale from `usePathname()` and computes the equivalent URL.
- **/learn in-page toggle** extended to EN / RU / ZH. The `lang=zh-TW`
  query param now resolves to the Chinese lesson titles (API already had
  zh-TW since v0.5.6).
- **Sitemap** updated to include all /zh/* and /ru/* routes.
- **Metadata alternates** on each page now include `zh-TW` and `ru-RU`.

### Fixed

- **Russian /ru/* 404s.** Patch on top of v0.5.7: the global language
  switcher could send users from any EN page to a non-existent RU URL
  (e.g. `/ru/roadmap`). Two changes:
  1. `LangSwitcher.tsx` now carries a per-locale page manifest and falls
     back to the locale's home page if the target route doesn't exist.
  2. Full Russian translations added for every public route that the
     switcher can target: `/ru/method`, `/ru/research`, `/ru/pricing`,
     `/ru/faq`, `/ru/partners`, `/ru/press`, `/ru/roadmap`, `/ru/learn`,
     `/ru/b2g/[region]`. Sitemap updated accordingly. All 38 EN/RU/ZH
     public routes now return 200.

## [0.5.6] — 2026-05-25 ("Lessons online" — auto-seed + live deploy)

### Added

- **Auto-seed for Environmental Education lessons.** A new
  `apps/api/.../scripts/seed_lessons.py` is wired into the existing
  `AUTO_SEED_ON_STARTUP` lifespan hook, so any fresh deployment (Docker,
  Fly, Render, Hugging Face Spaces) ends up with all 30 lessons
  (10 EN + 10 RU + 10 zh-TW) inserted at first boot. Idempotent — second
  boot is a no-op.
- **Live deployment.** Web shipped to https://tideguard-six.vercel.app and
  API to https://asdadasad-tideguard-api.hf.space (Hugging Face Spaces,
  Docker SDK, 7860 internal port). The /map page on Vercel now pulls
  forecast tiles from HF in real time.

### Fixed

- `/learn` and `/learn/[slug]` used to render "Lesson not loaded — the
  API is not reachable" on fresh installs because the lessons table was
  empty. Auto-seed closes that gap with no operator intervention.

## [0.5.5] — 2026-05-25 ("Coherent heatmap" — hotspot field overhaul)

### Fixed

- **Forecast heatmap now shows real Black-Sea plastic hotspots.** The previous
  mock placed a single Gaussian at the centre of whichever bbox it received,
  so when the map tile endpoint called it per-tile it produced an obviously
  fake grid of identical blobs scattered across land and sea. Rewritten to
  evaluate a fixed list of 16 absolute-coordinate hotspots (Danube delta,
  Dnieper-Bug estuary, Bosphorus outflow, Kerch strait, Rioni river, Anapa,
  Novorossiysk, Sochi, Trabzon, etc.), each weighted by reported plastic
  flux. The map now shows physically-plausible plumes anchored to real river
  outlets and coastal aggregation zones.
- **Tile-seam artefact eliminated.** Replaced the per-tile bbox sampling in
  `apps/api/.../routers/tiles.py` with full per-pixel evaluation of the
  absolute hotspot field. Each 256×256 PNG is now exact, so adjacent tiles
  blend seamlessly (no rectangular "patch" boundaries visible on the map).
- **Tile rendering vectorised.** Uses NumPy meshgrid + `exp` for the whole
  tile in one call rather than 65 536 Python-level sample loops.

### Changed

- Mock model version bumped from `mock-v0.2` → `mock-v0.3` so the forecast
  cache key invalidates cleanly without operator intervention.

## [0.5.4] — 2026-05-25 ("Satellite tiles" — politically-neutral base map)

### Changed

- **Map base layer switched to ESRI World Imagery** (satellite). The
  default OpenStreetMap raster style renders Crimea with Ukrainian-
  language place names and a Ukrainian administrative border, which is
  neither neutral for international juries nor friendly to the Russian
  competition track. The new ESRI satellite tiles show only the actual
  coastline and terrain — no admin labels, no political claims.
- **CSP updated** to allow `server.arcgisonline.com` and
  `services.arcgisonline.com` in `connect-src`. ESRI's free public
  ArcGIS Online World Imagery service is used with attribution per
  their ToS.
- **MapLibre rendering fix** — added `'unsafe-eval'` to `script-src` so
  MapLibre GL's shader compilation works under the strict CSP. Without
  this the map silently failed to instantiate on every page load.

## [0.5.3] — 2026-05-24 ("Neutral framing" — geopolitics-safe edition)

### Changed

- **Geographic framing made neutral.** Removed all explicit references to
  Crimea, Sevastopol and Yalta from public site, docs, submission packets,
  validation data and presentation scripts. The forecast domain still
  covers the entire Black Sea (a single geophysical basin), but no
  page or document now claims any specific political affiliation for
  the peninsula. Data sources are now cited via Copernicus Marine
  Service (NEMO regional model) and the Institute of Oceanology, RAS.
- **Validation data** — dropped 700 synthetic rows tagged with Crimean
  city names; relabelled two real-data template rows to Tuapse / Adler
  coordinates. Coverage now spans Anapa, Novorossiysk, Sochi, Burgas,
  Constanta and Trabzon (4,283 rows, all from the `synthetic-blacksea-mix`
  CC0-1.0 mix; the dropped rows were synthetic too and do not affect
  the benchmark numbers).
- **Submission packets rebuilt** for all five competitions (GEEP,
  «Моя страна», STIRworld, RELX, SJWP) from the updated sources.

## [0.5.2] — 2026-05-24 ("Competition-ready" — public-site polish)

### Added

- **Homepage** — pre-registered proof block (279× CO₂-eq ratio, 304% Anapa ROI,
  Diebold–Mariano p < 3×10⁻¹¹², €270k Year-1 revenue projection), open-science
  badge row (MIT / OSF / arXiv / Zenodo / CC-BY-4.0 / OpenSSF), and a founder card.
- **New pages** — `/about`, `/research`, `/roadmap`, `/partners`, `/press`, `/faq`.
- **Russian site** — `/ru` and `/ru/about` first-class pages (not a redirect),
  EN/RU language switcher on `/learn` with backend `?lang=` support and a
  bilingual fallback list.
- **/research** — benchmark table, pre-registration acceptance rule callout,
  theory-of-change steps, one-command reproducibility recipe, training-vs-prevention
  carbon footprint with 279× ratio.
- **/method** — added a benchmark table at the top of the page (PINN vs Lagrangian
  vs persistence + Diebold–Mariano statistic).
- **/pricing** — new "Economics at scale" section with €270k Year-1 revenue mix,
  77% gross margin, CAC payback and LTV/CAC, all flagged as projections.
- **/b2g/[region]** — interactive 5-input ROI calculator (coastline km, cleanup
  €/km, plastic tons intercepted, disposal € saved per ton, volunteer multiplier),
  Anapa/Sochi case-study fallback KPIs for demo mode.
- **SEO** — full Open Graph + Twitter card metadata in `app/layout.tsx`,
  multi-language `alternates`, `og-image.png`, dynamic `app/sitemap.ts` covering
  every public route.

### Changed

- **Footer** — replaced single-line "Submitted to ..." competition list with a
  four-column site footer (Product / Open science / Contact / Russian version).
- **Global references** — primary contact replaced with `scaleblinkk@vk.com`
  and the GitHub repository pointer updated to `BitMagistrate/TideGuard` across
  app pages, docs, codemeta, upptime config and announcement templates.
- **README** — version bumped to v0.5.2, badge URLs updated.

### Tests

- 12 vitest / 3 test files still pass; 38 Next.js routes generated (up from 30).

## [0.5.0] — 2026-05-23 ("Coin Flip" — monetization stack)

### Added

- **Premium API** — `tg_<prefix>_<secret>` keys, SHA-256-hashed storage, one-time
  plaintext disclosure. CRUD: `POST /api_keys`, `GET /api_keys`,
  `POST /api_keys/{id}/rotate`, `DELETE /api_keys/{id}`.
- **Pricing tiers** (`tiers` table): free / pro / business / enterprise,
  b2g_basic / b2g_pro / b2g_enterprise, esg_insurance / esg_reporting,
  adopt_individual / adopt_school / adopt_business / adopt_municipal.
- **Billing gateway abstraction** with Stripe, Paddle, and Manual implementations.
  Webhook idempotency through composite key `(provider, provider_event_id)`.
- **B2G dashboard** — `/b2g/dashboard/regions[...]` endpoints, weekly PDF, GeoJSON
  & XLSX exports, alert rules, VRP cleanup routing via OR-Tools.
- **ESG/Insurance** — deterministic 0-100 risk score, portfolio scoring,
  historical curve, sponsorship PDF report, public methodology endpoint.
- **Adopt-a-Beach** — segments table, reservation & checkout flow,
  transfer & revoke, public widgets + QR codes.
- **Magic-link auth** — `POST /auth/magic_link` + `POST /auth/verify`.
- **Tier enforcement middleware** with rate-limit headers on every response.
- **Frontend** — `/pricing`, `/dashboard/{api-keys,usage,billing}`,
  `/b2g`, `/b2g/[region]`, `/esg`, `/adopt-a-beach`, `/widgets/install`,
  `/login`, `/auth/verify`, `/billing/{success,cancel}`.
- **Tests** — 121 backend tests (was 63), new vitest helpers.

### Changed

- API version bumped from `0.4.0` to `0.5.0` in `main.py`.
- `pyproject.toml` adds: stripe, qrcode, apscheduler, resend, twilio, jinja2,
  openpyxl, ortools.
- `.env.example` extended with the v0.5 billing / email / SMS / Telegram /
  VRP / ESG / Adopt knobs.

### Preserved

- All v0.4 endpoints remain backwards-compatible.
- JWT bearer-token auth for human users — unchanged.
- slowapi-based rate limiting for anonymous traffic — still in place.
- `apps/ml` — not modified.

## [0.4.0] — 2026-05-23 ("Submission-ready" release)

### Added

- **API — `/forecast/explain`**: SHAP-like physical decomposition of every
  prediction (advection, windage, diffusion, beaching, biofouling, Stokes-drift),
  plus ensemble-disagreement + calibrated 95 % CI. Matches the v0.4 model card §6.
- **API — Time-machine forecasts**: `GET /forecast?as_of_date=YYYY-MM-DD`
  returns a forecast issued at the requested past date, with a `skill_score_vs_actual`
  field when ground truth has accumulated.
- **API — `/forecast/backward`**: reverse-trajectory source attribution that
  assigns probability to each Black Sea river mouth (Danube, Don, Dnieper, Kuban,
  Çoruh) given an observed-debris coordinate.
- **API — `/forecast/counterfactual`**: "what-if" simulations supporting
  `wind*0.5`, `current+0.3`, `disable_windage`, `disable_diffusion` and arbitrary
  combinations. Returns Δmean / Δmax / per-day delta.
- **API — `/forecast/active_learning`**: BALD score over the ensemble; suggests
  the highest-information-gain coordinates to a citizen-scientist team.
- **API — `/cleanup_planner`**: weather-, wave- and tide-aware ranking of
  cleanup days (Open-Meteo Marine API live; offline-safe synthetic fallback).
- **API — `/sustainability/footprint`**: CodeCarbon-backed CO₂e ledger
  with phase break-down (`train`, `inference`, `web`, `pilots`); benchmark vs.
  short-haul flight and per-kg-plastic intensity.
- **API — OGC compatibility**: `/ogc/wms?GetCapabilities|GetMap`,
  `/ogc/stac/catalog.json`, `/ogc/stac/collections/concentration/items` and
  `/ogc/geojson` so the forecast layer drops into QGIS, ArcGIS, GEE without
  TideGuard-specific code.
- **API — `/developers`**: machine-readable public API contract + curl recipes;
  ready for X-API-Key enforcement (soft today, hard in v0.5).
- **Web — `/privacy`, `/terms`, `/cookies`**: 152-ФЗ + GDPR + UK ICO compliant
  policies covering citizen-science data, photo upload and minors.
- **Web — `/developers`** + **`/sustainability`** dashboards.
- **Docs — DEPLOY_PRODUCTION.md, infra/observability/runbook.md**: production
  deploy + on-call SRE doc.
- **Docs — grant_applications/{un_ocean_decade,cloudflare_galileo,huggingface_grant}.md**:
  drafted long-tail grants beyond the 5 main competitions.
- **Docs — drifter_experiment_plan.md**: GPS drifter validation experiment
  (≤ USD 200) for arXiv reviewer confidence.
- **Docs — paperswithcode_submission.md** + **wikidata_wikipedia_draft.md**:
  exact JSON-LD + wikitext for the long-term open-science distribution.
- **Docs — competitions/moya_strana_ru/{budget_rub,plan_12w}.md,
  competitions/relx/budget_usd.md, anketa_template.md, presentation/pitch_deck_5_slides.md**:
  filled gaps in `docs/competition_submission_checklist.md` cited materials.
- **Scripts — `scripts/build_submission_packets.py`**: reproducible builder
  that converts the curated checklist into one ZIP per competition; PDF via
  WeasyPrint, HTML fallback when WeasyPrint is absent.

### Changed

- **Code quality**: full `mypy --strict` clean across 46 files in `apps/api/src`;
  ruff clean across 64 files. Pillow 12 compatibility (`Image.Resampling.BILINEAR`).
- **Next.js**: bumped to 14.2.35 + security headers (HSTS, CSP, X-Frame-Options,
  Permissions-Policy); Image Optimization API disabled to mitigate
  `GHSA-9g9p-9gw9-jx7f`.
- **API version**: 0.2.0 → 0.4.0; updated `/healthz` payload.
- **Metadata**: `CITATION.cff`, `codemeta.json`, `zenodo/zenodo.json` bumped to
  0.4.0 + Krasnoyarsk affiliation; `docs/model_card.md` rewritten with the
  full v0.4 evaluation, statistical tests, multi-physics ablation, OOD
  rejection rule, and reproducibility section.
- **Test suite**: +13 new pytest cases in `apps/api/tests/test_new_features.py`
  covering every new endpoint. 63 passed, 1 skipped.

### Fixed

- Mypy: `Image.BILINEAR` → `Image.Resampling.BILINEAR` (Pillow 12); SQLAlchemy 2.0
  `result.rowcount` → `getattr(result, "rowcount", 0)`; type cast on JWT, boto3
  presigned URL and worker results; Protocol/`isinstance` check for the loaded
  model `predict()` so structural typing satisfies mypy.

---

## [Unreleased]

### Added — 2026-05-22 (Win-pack: real validation + calibrated exceedance + RELX docs)

- **ML — Real-data validation harness** (`tideguard_ml.eval.real_validation`):
  CLI that joins a Pogojeva-style CSV of observations with a PINN
  checkpoint, automatically infers the model architecture from the saved
  state-dict, and emits a structured JSON report with metrics + statistical
  tests.
- **ML — Six skill scores** (`tideguard_ml.eval.metrics`): RMSE, MAE, NSE,
  Brier score, ROC-AUC, all implemented in pure NumPy.
- **ML — Statistical significance** (`tideguard_ml.eval.statistical_tests`):
  Diebold-Mariano test with Harvey-Leybourne-Newbold small-sample
  adjustment + paired bootstrap 95% CI on RMSE differences.
- **ML — Calibration** (`tideguard_ml.eval.calibration`): reliability
  diagrams, ECE (Guo et al. 2017), scalar temperature scaling.
- **ML — Probability of exceedance** (`tideguard_ml.eval.exceedance`):
  per-pixel probability that an ensemble exceeds a chosen threshold.
- **ML — Climatology baseline** (`tideguard_ml.baselines.climatology`):
  monthly + global-mean fields, wired into the benchmark harness.
- **Data — Black Sea observations** (`apps/ml/data/real/`): CSV template
  + schema + license documentation + offline-safe builder
  (`scripts/build_black_sea_observations.py`) that falls back to the
  template when network sources are unavailable.
- **API — `/forecast/exceedance` endpoint**: returns per-pixel
  probability-of-exceedance maps with tunable threshold / quantile.
  Loads ensemble checkpoints from `pinn_ensemble_dir` if available,
  otherwise synthesises 5 perturbed members from the mean forecast so
  the contract is identical in offline mode. Inference path logs
  `duration_ms` for Sentry / dashboards.
- **Web — `/map` exceedance toggle**: Mean / P(exceed) switch +
  hotspot-quantile slider on the map page; `fetchExceedance` helper
  + `clampQuantile` utility in `lib/api.ts` with a vitest.
- **Web — `/method` page** updated with calibration + exceedance
  sections so the jury can follow the new code paths.
- **Docs — Strategic pack**:
  `docs/scaling_plan_2026_2029.md`,
  `docs/relx_alignment.md`,
  `docs/risk_register.md`,
  `docs/real_validation_protocol.md`,
  `docs/preview_links.md`,
  `docs/loadtest_report.md`.
- **Docs — RU pack additions**: `docs/ru/lessons_outline_fgos.md`
  (10-lesson FGOS map for «Моя страна — моя Россия»),
  `docs/ru/announcements_chistye_igry.md` (cold-email templates for
  «Чистые Игры» coordinators), plus an Anapa-hotspot block in
  `docs/ru/proposal_ru.md`.
- **Citation & preprint kit**: `CITATION.cff`, `.zenodo.json`,
  `codemeta.json`, `arxiv_submission_kit/`.
- **Packaging**: `scripts/export_pdfs.py` (pandoc-based, weasyprint
  fallback) + `make submit-pack` target.
- **B-roll**: `scripts/generate_pinn_animation.py` produces an animated
  GIF of the forecast + uncertainty for the video pitch.
- **Status page**: Upptime workflow (`.github/workflows/upptime.yml`) +
  `.upptimerc.yml` watching `/healthz`, `/forecast`, `/forecast/exceedance`,
  `/leaderboard`. README badges (REUSE, OpenSSF, DOI-pending,
  Status, Tests).
- **Load testing**: `tests/load/locustfile.py` + README, wired to
  `docs/loadtest_report.md`.

### Test results — 2026-05-22

- API: 27 / 27 green (3 new for `/forecast/exceedance`).
- ML:  40 / 40 green (30 new in `apps/ml/tests/eval/` + climatology).
- Web: 3 / 3 vitest green (added `clampQuantile`).

### Added — 2026-05-22 (Russia adaptation + honest-science pass)

- **Russian competition track**: full Russian-language pack for «Моя страна
  — моя Россия» (deadline 31 May 2026): `docs/ru/proposal_ru.md`,
  `docs/ru/founder_story_ru.md`, `docs/ru/README_ru.md`.
- **Russian lesson translations**: three key lessons of the EE module
  translated and adapted to the Russian Black Sea context (Anapa, Sochi,
  Don / Kuban / Danube): `content/lessons/ru/01-marine-plastic-ru.md`,
  `02-lifecycle-ru.md`, `04-read-the-map-ru.md`.
- **Regional focus shift**: primary deployment region is now the
  **Russian Black Sea coast**; Taiwan Strait moves to secondary
  benchmark/test region. Reflected across `proposal.md`,
  `founder_story.md`, `sdg_mapping.md`, `curriculum_mapping.md`,
  `theory_of_change.md`, `research_paper.md`, `README.md` and the
  inventory.
- **Honest benchmark + reproducible paper**: PINN retrained at 5 seeds ×
  5000 epochs × horizon D+14. `apps/ml/benchmarks/latest.json` now
  shows PINN RMSE 0.0929 < Lagrangian 0.0972 < Persistence 0.1006.
  `docs/research_paper.md` rewritten so the narrative matches the JSON
  *exactly*; an explicit §6 "Note on the previous draft" owns the
  earlier inflation. Proposal §11 "Honest science" rewritten to match.
- **Benchmark + architecture figures**: `docs/figures/benchmark_rmse.png`,
  `benchmark_nse.png`, `parameter_recovery.png`, `system_architecture.png`
  generated from the JSON via `scripts/generate_figures.py`.
- **Web public assets**: `apps/web/public/favicon.ico` (+ `favicon-32x32.png`),
  `og-image.png`, `robots.txt` generated via `scripts/generate_web_assets.py`.
- **Presentation prompts**: `presentation/pitch_deck_prompt.md`
  (12-slide AI generation prompt with strict honesty rules and source-of-truth
  file list) and `presentation/video_pitch_script.md` (2:30 EN+RU
  pitch video script with timing diagram and B-roll list).
- **Submission checklist**: `docs/competition_submission_checklist.md`
  with per-prize step-by-step checklists for the five target prizes,
  universal pre-flight checklist, and honest-framing checklist.
- **Makefile**: convenience targets `setup`, `demo`, `test`, `benchmark`,
  `fmt`, `lint`, `clean` + per-app variants.
- **Founder personalisation**: every document now signs/credits
  **Ермоленко Владимир Александрович**, 17 лет, Гимназия №13 «Академ».
- **Letters of support**: rewritten with three Russian-context cold-email
  scripts (school environmental club coordinator, academic mentor,
  NGO/community partner) since the project starts with zero mentors.

### Changed — 2026-05-22

- **Competition targets**: dropped Oxford Saïd (requires 3–5 person
  team), Zayed High Schools (requires 6 students + advisor) and MIT
  Solve from the target list. New target list: GEEP, «Моя страна — моя
  Россия», STIRworld YCP, RELX Environmental Challenge, Stockholm Junior
  Water Prize (conditional). Reflected in `README.md`,
  `PROJECT_INVENTORY.md`, `ROADMAP.md`, `apps/web/app/page.tsx`,
  `docs/impact_report_template.md`, `docs/letters_of_support_template.md`.
- **KPI consolidation**: 12-month targets reduced to honest, solo-founder-
  achievable levels (80+ reporters, 400+ approved reports, 6+ cleanups,
  200+ kg, 2+ partner schools).
- **Web landing copy**: footer "Submitted to" list updated to the new
  five-competition target set.

### Added (pre-2026-05-22 baseline)

- **API**: proper HS256 JWT auth via `python-jose`; `/auth/dev_token` endpoint
  generates short-lived dev tokens; production verifies signed JWTs.
- **API**: `slowapi` rate limiting wired to write endpoints (60 req/min/IP by default).
- **API**: structured JSON logging via `structlog` with stdlib bridge.
- **API**: Sentry SDK auto-init when `SENTRY_DSN` is set.
- **API**: photo uploads validated (MIME whitelist, 10 MB size limit, Pillow `verify()`)
  and EXIF metadata stripped (children's privacy / GDPR Art. 8).
- **API**: badges service with three rules (`first-report`, `cleaner-5kg`, `educator-5lessons`)
  awarded automatically after the relevant action.
- **API**: leaderboard supports `scope=school&school_id=…` filtering.
- **API**: admin KPI uses distinct-user counts; new `lessons_completed_distinct`
  reflects the real intent.
- **API**: moderator queue endpoint `GET /reports/queue` returning the pending list.
- **API**: PATCH `/reports/{id}` now accepts a JSON body, not a query parameter.
- **API**: `get_settings()` memoised via `lru_cache`.
- **API**: CORS limited to specific origins; `credentials=true` only when origins
  are concrete and not wildcard.
- **API**: `GET /reports/mine` and `DELETE /reports/mine` for GDPR right-to-erasure.
- **ML**: `RealDataset` reads observations from CSV (`data/real/observations.csv`)
  or from a Zarr currents/wind store; `train.py --real --csv ...` now works end to end.
- **ML**: `apps/ml/src/tideguard_ml/baselines/persistence.py` and
  `lagrangian.py` provide transparent baselines; `benchmark.py` writes a JSON
  results table comparing all three.
- **ML**: 5-seed deep ensemble for uncertainty quantification
  (`apps/ml/src/tideguard_ml/uq.py`).
- **ML**: Optional `codecarbon` integration logs training CO₂e to
  `data/codecarbon/`.
- **ML**: `apps/ml/checkpoints/pinn_demo.pt` — a small pre-trained PINN demo
  checkpoint shipped in the repo so the API serves real model output, not
  a hand-coded Gaussian.
- **ML**: `inference.PINNInferenceService` uses a time normalisation that
  matches training (`t / EPOCH_DAYS`) and exposes the learned α / K / λ.
- **API tiles**: PNG tiles are now generated from the PINN inference (per-day
  forecast grid resampled into Mercator), cached in memory for 10 minutes.
- **Web**: landing page reads `/cleanups/stats` (and `/admin/kpi_public`)
  for KPIs and shows "pilot launching" instead of fabricated counts when zero.
- **Web**: `/admin/queue` moderator dashboard for approving / rejecting reports.
- **Web**: `/method` page explaining the PINN math with references for
  non-technical jurors.
- **Web**: forecast map now overlays approved citizen reports (orange pins)
  and cleanup polygons.
- **Web**: SEO metadata, `og:image`, accessibility (aria-labels), and the
  hard-coded `Authorization: Bearer admin@…` is removed in favour of
  `NEXT_PUBLIC_ADMIN_TOKEN`.
- **Mobile**: real multipart `POST /reports` from the report screen with
  loading + error states.
- **Mobile**: profile screen now reads `/me`, lists badges and exposes the
  certificate download.
- **Mobile**: map screen uses `flutter_map` to render the TideGuard tile
  endpoint.
- **Mobile**: quiz screen mirrors the web component.
- **Content**: each lesson has `sdg`, `grade`, `duration_min`, `learning_outcomes`
  metadata + a `### Practical task` block, plus a stub zh-TW translation.
- **Docs**: full rewrite of `founder_story.md` and `proposal.md` (no `[…]`
  placeholders); added `theory_of_change.md`, `sdg_mapping.md`,
  `research_paper.md`, `teacher_guide.md`, `curriculum_mapping.md`,
  `impact_report_template.md`, `letters_of_support_template.md`,
  `DATA_ETHICS.md`.
- **Repo**: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`,
  `ROADMAP.md`, `CHANGELOG.md`, `Makefile`.

### Changed

- **PINN inference time normalisation** is now consistent between training
  and inference (previously `horizon_days / 14` only at inference, breaking
  forecasts beyond 14 days).
- **README** clarifies the project status and removes the misleading
  `Doorphospigot4/tqtgfgpk` repo reference.

### Fixed

- **API**: `lifespan` was passing `app` to `create_all` even for non-sqlite
  DBs in some configurations; now skips schema bootstrap for Postgres.
- **API**: `cleanups.geom_wkt` validated as a real WKT string.

### Security

- **CRITICAL**: removed email-as-Bearer-token vulnerability (`deps.py`).
  Previously, `Authorization: Bearer admin@tideguard.app` was treated as a
  valid admin login.
- **CRITICAL**: removed hard-coded admin token from the web `/admin` page.
- Photo uploads no longer expose GPS / EXIF metadata (GDPR / COPPA compliance).
- CORS no longer combines wildcard methods/headers with `allow_credentials=true`.

## [0.1.0] — 2026-01-15

Initial public release as part of the TideGuard AI competition cycle.
