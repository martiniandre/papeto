# frontend/ — mobile rules

Read the root `AGENTS.md` first. This file adds app specifics.

## Stack

Expo (latest SDK) · TypeScript strict · Expo Router · Gluestack UI on NativeWind · TanStack Query (server state) ·
Zustand (local UI state only) · React Hook Form + Zod · i18next (`pt-BR` first) · expo-camera ·
expo-image-manipulator · expo-secure-store · expo-notifications · API client generated from the backend OpenAPI
(`openapi-typescript`). Pet animation: `<Pet mood events />` component; PNG placeholders now, Rive later
(state machine `Pet`, view model `PetVM`).

## Layout

```
app/            Expo Router routes: (onboarding)/, (tabs)/home, (tabs)/history, (tabs)/profile, meal/, premium/
src/components/ shared UI (wrapping Gluestack), Pet, Hearts, MealCard...
src/features/   per feature: hooks, screens parts, schemas
src/api/        generated client + TanStack Query hooks
src/i18n/       pt-BR.json (all user-facing text lives here)
src/theme/      tokens (colors, spacing, radii, type)
assets/pet/     happy.png, tired.png, sleepy.png, fainted.png, paused.png (placeholders)
```

## Rules

- The app never computes game rules. It renders `mood`, `lives` and `events` from the API.
- All text from i18n. No hard-coded Portuguese strings in components.
- Design tokens: primary `#4F46E5`, background `#F8F9FC`, text `#171B2E`, secondary text `#5E6478`, borders on inputs `#7D839A`, points amber `#FCEBC0`/`#4A3410`. Font Nunito.
- Accessibility: `accessibilityLabel` on icon-only buttons; touch targets >= 44; use `minHeight`, never fixed heights on text containers; selected state not by color only; `accessibilityState` on toggles and tabs; announce analysis progress; respect `AccessibilityInfo.isReduceMotionEnabled` (static pet image).
- Photos: resize to max 1024 px before upload; never save to the gallery or cache permanently.
- Navigation and states follow `docs/screens.md`. Every data screen handles loading, offline and error.
- Tokens only in `expo-secure-store`. Never log tokens or photos.
- Tests: Jest + React Native Testing Library for components and hooks; test accessibility labels.

## Commands

```
npm install
npx expo start
npm run typecheck && npm run lint && npm test
npm run api:types      # regenerate the API client from http://localhost:8000/openapi.json
```
