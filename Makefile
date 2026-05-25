# TideGuard AI — convenience targets
#
# Quick start:
#   make setup     # install all dependencies (uv, pnpm, flutter)
#   make demo      # train tiny PINN, seed lessons, run API + web locally
#   make test      # run API (24), ML (10), web vitest, flutter analyze
#   make benchmark # 5-seed × 5000-epoch PINN vs persistence vs lagrangian
#
# All targets are idempotent and safe to re-run.

PY ?= python3
UV ?= uv
PNPM ?= pnpm
FLUTTER ?= flutter

API_DIR := apps/api
ML_DIR := apps/ml
WEB_DIR := apps/web
MOBILE_DIR := apps/mobile

.PHONY: help setup setup-api setup-ml setup-web setup-mobile \
        demo demo-api demo-web demo-seed demo-train \
        test test-api test-ml test-web test-mobile \
        benchmark train-ensemble real-validation \
        clean clean-cache check-tools fmt lint

help:
	@echo "TideGuard AI — Makefile targets"
	@echo ""
	@echo "  setup      Install all dependencies (uv, pnpm, flutter pub get)"
	@echo "  demo       Train tiny PINN, seed lessons, run API + web locally"
	@echo "  test       Run all test suites (API 24 + ML 10 + Web vitest + flutter analyze)"
	@echo "  benchmark  Reproduce 5-seed × 5000-epoch benchmark"
	@echo "  fmt        Run ruff/prettier autoformat across the repo"
	@echo "  lint       Run ruff + eslint + flutter analyze without modifying files"
	@echo "  clean      Remove build artifacts and __pycache__"
	@echo ""
	@echo "Per-app targets: setup-api, setup-ml, setup-web, setup-mobile,"
	@echo "                 test-api, test-ml, test-web, test-mobile,"
	@echo "                 demo-api, demo-web, demo-seed, demo-train."

# ------------------------------------------------------------------
# setup
# ------------------------------------------------------------------

setup: check-tools setup-api setup-ml setup-web setup-mobile
	@echo "[setup] ALL DONE"

setup-api:
	@echo "[setup-api] $(API_DIR)"
	cd $(API_DIR) && $(UV) venv && $(UV) pip install -e ".[dev]"

setup-ml:
	@echo "[setup-ml] $(ML_DIR)"
	cd $(ML_DIR) && $(UV) venv && $(UV) pip install -e ".[dev]"

setup-web:
	@echo "[setup-web] root + workspaces"
	$(PNPM) install

setup-mobile:
	@echo "[setup-mobile] $(MOBILE_DIR)"
	cd $(MOBILE_DIR) && $(FLUTTER) pub get

check-tools:
	@command -v $(UV) >/dev/null 2>&1 || { echo "uv not found. Install: https://github.com/astral-sh/uv"; exit 1; }
	@command -v $(PNPM) >/dev/null 2>&1 || { echo "pnpm not found. Install: https://pnpm.io/installation"; exit 1; }
	@command -v $(FLUTTER) >/dev/null 2>&1 || echo "[warn] flutter not found — skipping mobile setup will still proceed."

# ------------------------------------------------------------------
# demo
# ------------------------------------------------------------------

demo: demo-train demo-seed
	@echo "[demo] starting API + web in foreground."
	@echo "[demo] API:   http://localhost:8000/docs"
	@echo "[demo] Web:   http://localhost:3000"
	@$(MAKE) -j 2 demo-api demo-web

demo-train:
	@echo "[demo-train] tiny PINN, 200 epochs, single seed (~1 minute)"
	cd $(ML_DIR) && $(UV) run python -m tideguard_ml.train --synthetic --epochs 200 --save checkpoints/pinn_demo.pt

demo-seed:
	@echo "[demo-seed] seeding lessons (curl, after API is up)"
	@bash -c 'sleep 2; curl -fs -X POST http://localhost:8000/education/_seed >/dev/null && echo "[demo-seed] lessons seeded" || echo "[demo-seed] could not reach API yet"' &

demo-api:
	cd $(API_DIR) && $(UV) run uvicorn tideguard_api.main:app --reload --port 8000

demo-web:
	$(PNPM) --filter @tideguard/web dev

# ------------------------------------------------------------------
# test
# ------------------------------------------------------------------

test: test-api test-ml test-web test-mobile
	@echo "[test] ALL GREEN"

test-api:
	@echo "[test-api] pytest (27 expected)"
	cd $(API_DIR) && $(UV) run pytest -q

test-ml:
	@echo "[test-ml] pytest (40 expected: 10 baseline + 30 eval/climatology)"
	cd $(ML_DIR) && $(UV) run pytest -q

test-web:
	@echo "[test-web] vitest"
	$(PNPM) --filter @tideguard/web test

test-mobile:
	@echo "[test-mobile] flutter analyze"
	cd $(MOBILE_DIR) && $(FLUTTER) analyze

# ------------------------------------------------------------------
# benchmark
# ------------------------------------------------------------------

benchmark:
	@echo "[benchmark] 5 seeds × 5000 epochs × horizon 14 — expect ~30-60 minutes on CPU"
	cd $(ML_DIR) && $(UV) run python -m tideguard_ml.baselines.benchmark --seeds 5 --epochs 5000 --horizon 14
	@echo "[benchmark] results written to apps/ml/benchmarks/latest.json"

train-ensemble:
	@echo "[train-ensemble] 5-seed UQ ensemble, 5000 epochs each"
	cd $(ML_DIR) && $(UV) run python -m tideguard_ml.train --synthetic --seed-ensemble 5 --epochs 5000

real-validation:
	@echo "[real-validation] PINN vs persistence vs climatology on real CSV"
	cd $(ML_DIR) && $(UV) run python -m tideguard_ml.eval.real_validation \
	    --csv data/real/black_sea_template.csv \
	    --checkpoint checkpoints/pinn_demo.pt \
	    --bbox 27,40,42,47 \
	    --out reports/real_validation_latest.json

# ------------------------------------------------------------------
# fmt / lint
# ------------------------------------------------------------------

fmt:
	@echo "[fmt] ruff format + prettier"
	cd $(API_DIR) && $(UV) run ruff format src tests
	cd $(ML_DIR) && $(UV) run ruff format src tests
	$(PNPM) --filter @tideguard/web exec prettier --write "{app,components,lib,public}/**/*.{ts,tsx,json,md}" 2>/dev/null || true

lint:
	@echo "[lint] ruff + eslint + flutter analyze"
	cd $(API_DIR) && $(UV) run ruff check src tests
	cd $(ML_DIR) && $(UV) run ruff check src tests
	$(PNPM) --filter @tideguard/web lint 2>/dev/null || true
	cd $(MOBILE_DIR) && $(FLUTTER) analyze 2>/dev/null || true

# ------------------------------------------------------------------
# clean
# ------------------------------------------------------------------

clean: clean-cache
	rm -rf $(API_DIR)/.venv $(ML_DIR)/.venv
	rm -rf $(WEB_DIR)/.next $(WEB_DIR)/node_modules node_modules
	rm -rf $(MOBILE_DIR)/build $(MOBILE_DIR)/.dart_tool
	rm -rf $(ML_DIR)/checkpoints/pinn_demo.pt

clean-cache:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .ruff_cache -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
