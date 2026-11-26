# One image for the API and the ARQ worker (Fly.io process groups pick the command).
# Build from be/:  docker build -t papeto-backend .
# No secrets are baked in: every setting comes from environment variables at runtime.

# ---- build: install locked dependencies with uv into /app/.venv ----
FROM python:3.12-slim-bookworm AS build

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Dependencies first (cached while pyproject.toml and uv.lock do not change). No dev tools.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

# ---- runtime: slim image, non-root user, no build tools ----
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    WEB_CONCURRENCY=2

RUN groupadd --system papeto && useradd --system --gid papeto --home-dir /app papeto

WORKDIR /app
COPY --from=build --chown=papeto:papeto /app /app

USER papeto
EXPOSE 8000

# API (default). Gunicorn reads WEB_CONCURRENCY for the number of Uvicorn workers.
# The ARQ worker runs from the same image: `arq app.worker.settings.WorkerSettings`.
# Migrations run from the same image: `alembic upgrade head`.
CMD ["gunicorn", "app.main:create_app()", "--worker-class", "uvicorn_worker.UvicornWorker", \
     "--bind", "0.0.0.0:8000", "--graceful-timeout", "30", "--timeout", "60"]
