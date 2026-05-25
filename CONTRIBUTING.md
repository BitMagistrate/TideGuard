# Contributing to TideGuard AI

Thank you for considering contributing! TideGuard is built by students,
for students — and every PR, issue, translation or pilot report is valued.

## Quick start

```bash
git clone <this repo>
pnpm install              # web + workspace lockfile
cd apps/api && uv venv && uv pip install -e ".[dev]"
cd ../ml && uv venv && uv pip install -e ".[dev]"
```

## Code

- **Backend (Python 3.11+)**: FastAPI, SQLAlchemy, Pydantic. Lint: `ruff`.
  Tests: `pytest`. Working dir: `apps/api/`.
- **ML (Python 3.11+)**: PyTorch, xarray, numpy. Lint: `ruff`. Tests:
  `pytest`. Working dir: `apps/ml/`.
- **Web (TypeScript)**: Next.js 14, Tailwind, MapLibre. Lint: `next lint` +
  `eslint`. Tests: `vitest`. Working dir: `apps/web/`.
- **Mobile (Dart)**: Flutter 3, Riverpod, go_router. Lint: `flutter analyze`.
  Tests: `flutter test`. Working dir: `apps/mobile/`.

Before pushing, run pre-commit:

```bash
pre-commit run --all-files
```

## Issues

- Use the **Bug** template for reproducible issues.
- Use the **Feature** template for new ideas.
- Tag `good-first-issue` if you're looking for a starter task.

## Pull requests

1. Fork the repo and create a branch from `main`.
2. Make your changes. Add tests if you add code.
3. Run all linters and tests. CI will also run them.
4. Open a PR with a clear title and description.

## Content (lessons, translations)

Lessons live in `content/lessons/`. Front matter follows a strict schema:

```yaml
---
slug: my-lesson
title: My lesson title
order: 11
xp: 50
sdg: [14, 4]
grade: [7, 8, 9, 10, 11, 12]
duration_min: 8
learning_outcomes:
  - "Outcome 1"
  - "Outcome 2"
---
```

Translations go into `content/lessons/zh-TW/`, `content/lessons/vi/` etc.
If you are a native speaker, please review machine-translated content and
mark corrections in a PR.

## Code of Conduct

We follow the [Contributor Covenant 2.1](CODE_OF_CONDUCT.md). Please
read it before participating.

## License

By contributing you agree that your contributions will be licensed under:
- MIT for code.
- CC-BY-4.0 for lesson content.
