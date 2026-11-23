# AGENTS.md — Papeto

Instructions for any AI coding agent (Claude Code, Codex, Cursor, Copilot, Gemini) working in this repository.
Humans: this is also the fastest way to understand the project.

## What we are building

Papeto is a mobile app (iOS and Android) where the user cares for a virtual pet, **Bolinha**, that lives on the
user's consistency in **logging meals by photo**. An AI describes the plate. The MVP is meal logging only.
Target: adults 18+, Brazil, UI in Brazilian Portuguese.

## Sources of truth (read before coding)

Read only what the task needs, in this order of precedence. When two sources disagree, the higher one wins.

1. `docs/domain/pet-rules.md` — canonical game rules (lives, mood, streak, points, limits). **Always read before touching pet, meals or points.**
2. `docs/product-rules.md` — hard product, safety and privacy rules distilled from the scope and legal docs.
3. `docs/decisions.md` — architecture decisions (ADRs) already taken. Do not reopen them without being asked.
4. `docs/screens.md` — screens, numbering, navigation flow and the states every screen must handle.
5. `docs/api.md` — API contract for the MVP.
6. `docs/scope.md` — full requirements and scope document (exported snapshot). It is long and has history:
   sections about **workouts (Treino), arena, social and calories are later phases or superseded**.
   The MVP is the meal-logging pet ("MVP pela alimentação").

Live versions (may be newer than the snapshot): scope doc https://claude.ai/artifact/LTBCF9VPoJm4S6jauwhivS ·
design canvas https://claude.ai/artifact/1kwmN9FBtScfqXR6yRmJ2N (pages Layout and Fluxo) ·
legal draft https://claude.ai/artifact/Dk8YdzqynRskhEP5iU4Az1.

If a rule you need is missing or ambiguous, **stop and ask**. Do not invent game rules, prices, limits or legal text.

## Hard rules (never break)

- **No calories, macros, weight, height, BMI, body measurements or meal scores** anywhere: code, API, database, UI, logs, analytics, AI prompts. Never label food as healthy/unhealthy. Points are only ever positive.
- **Meal photos are never stored.** Resize, send to the vision provider, discard. Never log image bytes or URLs.
- **18+ only.** Meal data requires the `meal_data` consent; without it, meal endpoints return 403.
- Language in the UI: say "registrar", never "comer" or "alimentar" (lives drop for lack of a log, not lack of food).
- Export and delete account are always free and never behind Premium.
- All code, identifiers, database names, API routes, JSON fields, error codes, comments, commits and branch names are in **English**. User-facing text only in i18n files (`pt-BR` first).
- Secrets only from environment variables. Never commit `.env` or keys. Never print secrets.
- No new external service or SDK without a port (see Architecture). Never import a provider SDK outside `providers/`.

## Repository layout

```
be/             FastAPI backend (Python 3.12, uv)            -> see be/AGENTS.md
frontend/       Expo React Native app (TypeScript)           -> see frontend/AGENTS.md
docs/           Scope, rules, decisions, screens, prompts
.github/        CI workflows and Copilot instructions
```

## Architecture in one paragraph

Ports and Adapters. The domain (`be/app/domain`) is pure Python with no framework imports. Every external
service enters through a port (Protocol) in `be/app/ports`: `FoodVisionProvider`, `PaymentProvider`,
`PushProvider`, `AuthProvider`, `StorageProvider`, `EmailProvider`, `AnalyticsProvider`, `ErrorReporter`,
`Clock`, `IdGenerator`. Real and fake adapters live in `be/app/providers`. import-linter enforces the
boundaries. The pet's mood is **computed on read**, never stored. The app only renders what the API returns.

## Commands

```
# backend
cd be && docker compose up -d          # Postgres + Redis
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
uv run pytest
uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run lint-imports

# app
cd frontend && npm install
npx expo start
npm run typecheck && npm run lint && npm test
```

## How to work

1. Restate the task in one or two lines and list the files you will touch. For anything larger than a small fix, show the plan first and wait.
2. Work in small steps. One concern per commit. Conventional Commits in English (`feat(be): add daily usage limit`).
3. Write or update tests in the same change. Domain rules need unit tests with the fake `Clock`, including timezone and DST edges.
4. Run the checks for the part you changed before saying you are done.
5. If you changed a rule, an endpoint or a screen flow, update the matching file in `docs/` in the same change.

## Definition of done

- Checks pass (lint, types, tests, import-linter).
- No hard rule broken. No secrets, no photo persistence, no calorie/score concept introduced.
- User-facing strings are in i18n files, accessible (labels on icon buttons, touch targets >= 44, no fixed heights on text containers, respects reduced motion).
- Docs updated when behavior changed.
