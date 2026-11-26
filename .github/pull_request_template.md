## What and why

<!-- One or two lines. Link the relevant docs/ section if a rule or flow changed. -->

## Definition of done (AGENTS.md)

- [ ] Checks pass for the parts I changed (backend: ruff check, ruff format --check, mypy, import-linter, pytest; app: typecheck, lint, tests)
- [ ] Tests added or updated in this change
- [ ] No hard rule broken: no calories, macros, weight, BMI or meal scores; no label of food as healthy/unhealthy
- [ ] No meal photo persisted, logged or cached (no image bytes or URLs in logs)
- [ ] No secrets, `.env` files or keys committed
- [ ] User-facing text lives in i18n files (`pt-BR` first); "registrar", not "comer" or "alimentar"
- [ ] Accessibility: labels on icon-only buttons, touch targets >= 44, no fixed heights on text containers, reduced motion respected
- [ ] Docs in `docs/` updated if a rule, endpoint or screen flow changed
