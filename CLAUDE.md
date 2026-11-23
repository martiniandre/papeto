@AGENTS.md

## Claude Code notes

- The rules above are the project rules. This file only adds Claude-specific habits.
- Before editing pet, meal or points code, read `docs/domain/pet-rules.md` with the Read tool.
- For multi-step work, keep a task list and show the plan before writing code.
- Prefer small, reviewable diffs. Do not reformat files you are not changing.
- Never read or print `.env` files (also blocked in `.claude/settings.json`).
- Folder-specific rules: `be/AGENTS.md` and `frontend/AGENTS.md` (imported by `be/CLAUDE.md` and `frontend/CLAUDE.md`).
