# Architecture decisions

Short ADR log. Status is "accepted" unless noted. Reopen only when asked.

| # | Decision | Why |
| --- | --- | --- |
| 001 | Monorepo with `be/` (FastAPI) and `frontend/` (Expo) | One place for docs and rules; agents see both sides |
| 002 | Backend: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 async, Alembic, Postgres | Typed, async, OpenAPI for free |
| 003 | Jobs: Redis + ARQ (not Celery) | Async-native, built-in cron, small footprint. Celery only if the queue grows |
| 004 | Pet mood computed on read; lives settled lazily (`settle`) | Same result on any device; no cron dependency for game state |
| 005 | Ports and Adapters for every external provider, enforced by import-linter | Swap Stripe, vision provider, push, etc. without touching the domain |
| 006 | Payments: Stripe first, behind `PaymentProvider`; webhooks idempotent by `external_event_id` | Brazil allows alternative payments in apps; easy to switch |
| 007 | Meal photos are never stored | Privacy (LGPD sensitive data) and cost |
| 008 | Deploy: Fly.io region `gru` (API, ARQ worker, Postgres), Upstash Redis, Expo EAS for the app; optional Cloudflare at the edge | Low cost, Brazil region, Docker-based |
| 009 | App: Expo + TypeScript strict, Expo Router, Gluestack UI on NativeWind, TanStack Query, Zustand (local only), React Hook Form + Zod, i18next | Fast iteration, accessible components |
| 010 | Pet animation: Rive state machine "Pet" with view model `PetVM` (mood enum, triggers celebrate/lifeLost/wakeUp, reduceMotion); PNG placeholders until the Rive file exists | App only sets inputs; animation logic stays in the file |
| 011 | Everything technical in English; UI in pt-BR via i18n | Consistency for code, logs and agents |
| 012 | Free plan: 2 AI photos per day. Pause is Premium | Product decision (25/11/2026) |
| 013 | Sign-in: email and **Google only** for now; **no email confirmation**; **no birth date** (the 18+ checkbox is enough). Google ID tokens are verified on the server with PyJWT + httpx against Google's JWKS, behind `AuthProvider` (no Google SDK). A Google account is linked to an existing account only by a Google-verified email. Apple comes later: the App Store requires Sign in with Apple once another social login exists, so it is **needed before any iOS release** | Product decision (26/11/2026). Less friction at sign-up; age gate stays the self-declared confirmation plus the store age signal |
