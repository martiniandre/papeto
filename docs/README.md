# docs

| File | What it is | Read when |
| --- | --- | --- |
| `domain/pet-rules.md` | Canonical game rules: lives, mood, streak, points, limits | Any change to pet, meals or points |
| `product-rules.md` | Safety, consent, privacy, retention and payment rules for the code | Anything touching user data, AI, payments or copy |
| `decisions.md` | Architecture decisions already taken | Before proposing a new library, service or pattern |
| `screens.md` | Screens, flows and states every screen must handle | Building or changing UI and navigation |
| `api.md` | API contract for the MVP | Building endpoints or the app client |
| `scope.md` | Full requirements snapshot (long, has history) | Background and requirement IDs (RF-xx) |
| `prompts/` | Prompts for the coding agent and for Rive | Starting the project; animating the pet |

Precedence when docs disagree: pet-rules > product-rules > decisions > screens > api > scope.
Update the matching doc in the same change when behavior changes.
