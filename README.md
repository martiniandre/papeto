# Papeto

Mobile app where you care for Bolinha, a virtual pet that lives on your consistency in logging meals by photo.

- `be/` — FastAPI backend (Python, uv)
- `frontend/` — Expo React Native app (TypeScript)
- `docs/` — scope, game rules, product rules, decisions, screens, API contract, prompts

Rules for contributors and AI agents: [AGENTS.md](AGENTS.md). Start with [docs/README.md](docs/README.md).
To scaffold the code with an agent, use [docs/prompts/bootstrap.md](docs/prompts/bootstrap.md).

## Vision provider and evaluation

The vision provider is not chosen yet. The backend runs the offline fake by default (`VISION_PROVIDER=fake`), and every
provider sits behind the same pipeline (`be/app/vision`: type and size check, 1024 px JPEG without metadata, one retry
on timeout, validation). Details: [docs/api.md](docs/api.md#vision-pipeline-beappvision).

**Plugging in a provider.** If it speaks the OpenAI-compatible `chat/completions` format, no code is needed: set
`VISION_PROVIDER=openai_compatible`, `VISION_API_KEY`, `VISION_MODEL` and `VISION_BASE_URL` in the environment (the
container refuses to start if one is missing). Otherwise add one file `be/app/providers/vision_<name>.py` with
`provider_name`, `model_version`, `prompt_version` and `async analyze(image, language)`, send `build_prompt(language)`
from `app/vision/prompt.py`, parse the answer with `app/vision/parsing.parse_answer`, add it to
`build_vision_adapter` in `be/app/container.py` and to the `VISIONS` list in the contract tests. Then update the
vendor table in the Privacy Policy and `docs/product-rules.md`.

**Evaluating a provider on ~30 dishes.** Photos never go in the repo. Keep them in a local folder outside it:

```
~/papeto-eval/
  01-arroz-feijao.jpg
  01-arroz-feijao.json   {"meal_type": "lunch", "food_groups": ["grains", "legumes", "vegetables"],
                          "items": ["arroz", ["feijão", "feijão preto"], "salada"]}
  02-pao-com-ovo.jpg
  02-pao-com-ovo.json    ...
```

Aim for about 30 dishes that look like real use: Brazilian lunch plates (PF), breakfast (pão, café, frutas), snacks,
dinners, a few blurry or dark photos, and two or three photos that are not food. An entry in `items` may be a list of
accepted names. Then, with the provider variables exported in your shell:

```
cd be
uv run python -m app.tools.vision_eval ~/papeto-eval            # table per dish + summary
uv run python -m app.tools.vision_eval ~/papeto-eval --json     # machine-readable report
```

It prints provider, model and prompt version, then meal_type accuracy, food_groups exact match, precision and
recall, item recall and mean seconds per photo. Failed analyses count as misses. Bump `PROMPT_VERSION` whenever the
prompt changes and keep the reports to compare runs.
