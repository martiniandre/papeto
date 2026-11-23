# be/ — backend rules

Read the root `AGENTS.md` first. This file adds backend specifics.

## Layout

```
app/
  main.py         FastAPI app factory, routers, middleware
  config.py       pydantic-settings (all env vars here, typed)
  container.py    dependency wiring: picks real or fake adapters from settings
  domain/         pure rules (pet, lives, points, limits). No FastAPI, SQLAlchemy, httpx or SDK imports
  ports/          Protocols for every external service + Clock and IdGenerator
  providers/      adapters: fake_*.py (tests/local) and real ones (stripe_payment.py, vision_<name>.py, expo_push.py...)
  services/       use cases that orchestrate domain + ports + repositories (e.g. log_meal.py)
  db/             SQLAlchemy models, repositories, Alembic migrations
  api/            routers and request/response schemas only (no business rules)
  worker/         ARQ settings and tasks (notifications only; never changes lives)
tests/
  unit/           domain tests with fake Clock (no DB)
  contract/       one suite per port, run against every adapter
  integration/    API + Postgres + Redis via Testcontainers
```

## Rules

- Import direction: `api → services → domain/ports`; `providers` implement `ports`; `db` is used by `services` through repositories. import-linter contracts in `pyproject.toml` must stay green.
- Domain functions take `today_local: date` / `now: datetime` as arguments (from `Clock`). Never call `datetime.now()` in domain or services.
- All datetimes stored in UTC (`timestamptz`); local days computed with `zoneinfo` from `user.timezone`.
- Every migration is reversible and reviewed. Never edit an applied migration.
- Error responses use stable codes from `app/api/errors.py`.
- Webhooks: verify signature first, then insert `payment_event` with unique `external_event_id`; duplicate → 200 without reprocessing.
- The vision adapter: resize with Pillow (max 1024 px, JPEG), send, validate with Pydantic, retry once on timeout, never persist or log the image.
- Logs are structured (structlog) and must not contain emails, tokens, photos or meal descriptions.
- mypy strict. No `Any` in domain or ports.
- Tests: every rule in `docs/domain/pet-rules.md` has a unit test; every port has a contract test.

## Commands

```
docker compose up -d
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
uv run pytest
uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run lint-imports
uv run alembic revision --autogenerate -m "short description"
```
