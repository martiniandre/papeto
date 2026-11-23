# Bootstrap prompt

Paste this into the coding agent at the repository root, after cloning. The agent already gets the project rules from
`AGENTS.md` / `CLAUDE.md`; this prompt only says what to build first.

---

Read `AGENTS.md`, `be/AGENTS.md`, `frontend/AGENTS.md`, `docs/domain/pet-rules.md`, `docs/product-rules.md`,
`docs/api.md` and `docs/screens.md`. Then build the project foundation in three stages. Stop after each stage so I can review.

**Stage 1 — backend (`be/`)**
- `uv` project with the stack from `docs/decisions.md`, `docker-compose.yml` (Postgres + Redis), `Dockerfile`, `fly.toml` (region `gru`, processes `api` and `worker`, `release_command` for migrations) and `.env.example`.
- The folder layout from `be/AGENTS.md`, with all ports and fake adapters, plus empty skeletons (TODO) for `stripe_payment.py` and `vision_provider.py`.
- Models and the first Alembic migration for: user, consent, pet (with `lives`, `streak_days`, `last_log_day`, `settled_on`, `rest_until`, `name`, `color`), meal_log, points_event, push_token, daily_usage, subscription, payment_event.
- Domain: everything in `docs/domain/pet-rules.md`, with the required tests.
- Endpoints from `docs/api.md`, using the fake vision provider. `POST /v1/meals` runs end to end.
- import-linter contracts, ruff, mypy strict.
- Done when: `docker compose up -d && uv run alembic upgrade head && uv run pytest` pass, plus lint, types and import-linter.

**Stage 2 — app (`frontend/`)**
- Expo project with the stack and layout from `frontend/AGENTS.md`, theme tokens, i18n `pt-BR`, generated API client.
- Screens for flows 1 (first access) and 2 (log a meal) from `docs/screens.md`, plus the tabs Home, History and Profile with loading, offline and error states.
- `<Pet>` component with the PNG placeholders, driven by `mood` and `events` from the API.
- Done when: the app runs in Expo Go against the local API and goes from sign-up to the first meal result; `typecheck`, `lint` and tests pass.

**Stage 3 — CI**
- GitHub Actions: backend (ruff, mypy, import-linter, pytest with Testcontainers) and app (typecheck, lint, tests) on every pull request.

Before writing code in each stage, show me the file tree you will create and anything in the docs that looks ambiguous or contradictory.
