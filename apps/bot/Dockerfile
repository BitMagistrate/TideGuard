FROM python:3.11-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN pip install --no-cache-dir uv

COPY apps/bot/pyproject.toml apps/bot/README.md /app/
COPY apps/bot/src/ /app/src/

RUN uv venv && uv pip install -e .

CMD ["uv", "run", "python", "-m", "tideguard_bot"]
