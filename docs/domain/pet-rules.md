# Pet rules (canonical)

This file is the single source of truth for the game rules. Code in `be/app/domain/` implements exactly this,
and every rule here has a unit test. If `docs/scope.md` says something different, this file wins (the scope doc
still has older workout-based rules).

Values marked *(tunable)* are starting values to test with users. Keep them in one config object, not scattered.

## Glossary

| Term | Meaning |
| --- | --- |
| log | A meal registered successfully: an AI analysis that succeeded and was saved, or a meal entered by hand when the photo could not be read (RF-95). Failed analyses are not logs. |
| local day | Calendar day in the user's IANA timezone (`user.timezone`). Day boundaries are local midnight. |
| missed day | A local day that ended with zero logs while the pet was not paused. |
| pause | Premium feature. `pet.rest_until` in the future means the pet is paused. |

## Lives

| Rule | Value |
| --- | --- |
| Starting lives | 2 |
| Maximum lives | 4 |
| Gain | +1 life for every 7 consecutive local days with at least one log *(tunable)*, up to the maximum |
| Loss | -1 life for each missed day |
| Pause | No life loss and the streak is kept while paused |
| Zero lives | Pet is fainted. The next log wakes it with exactly 1 life |
| Daily AI limit | Hitting the photo limit never costs a life (the day already has a log, or the user can log tomorrow) |

### How lives are settled (no cron dependency)

The pet stores `lives`, `streak_days`, `last_log_day` (local date of the last log) and `settled_on`
(last local date for which missed days were applied). On every read and every write, call
`settle(pet, today_local)`:

1. For each local day `d` from `settled_on + 1` to `today_local - 1` (inclusive):
   - if `d` had a log: nothing (already counted when the log happened);
   - else if the pet was paused on `d`: nothing;
   - else: `lives = max(0, lives - 1)` and `streak_days = 0`.
2. Set `settled_on = today_local - 1`.

`settle` is pure (takes the pet, the set of logged days and pause windows, and the date) and idempotent.
The ARQ cron job only sends notifications; it never changes lives.

### On a new log (local day `t`)

1. `settle(pet, t)`.
2. If `lives == 0`: `lives = 1`, emit event `wake_up` (+5 points, once per wake-up).
3. If `last_log_day != t`:
   - `streak_days = streak_days + 1` if `last_log_day == t - 1` (or the days between were paused), else `1`;
   - if `streak_days % 7 == 0` and `lives < 4`: `lives += 1`, emit `celebrate`.
4. `last_log_day = t`. Add points (below).

## Mood (computed on read, never stored)

Evaluated in this order; the first match wins:

| Mood | Condition |
| --- | --- |
| `paused` | `rest_until` is in the future |
| `fainted` | `lives == 0` |
| `happy` | at least one log today (local) |
| `sleepy` | `lives == 1` |
| `tired` | otherwise (no log today, 2 or more lives) |

Events returned by `POST /v1/meals` and `GET /v1/pet` so the app can play one-shot animations:
`wake_up`, `life_lost` (lives dropped since the client's last seen value), `celebrate` (gained a life),
`level_up` (level rose since the client's last seen level, see Levels and attributes).

> Note: the scope doc's state table still describes "sleepy = 2 days without logging". With 2 starting lives
> that collides with fainting, so this file uses lives instead. Update the scope doc if this is confirmed.

## Points

| Event | Points |
| --- | --- |
| Meal logged | +10, at most 3 scored meals per local day *(tunable)* |
| Wake up after fainting | +5, once per wake-up |
| Correcting or deleting a meal | 0 (points never change after the fact, never negative) |

Points are stored as `points_event` rows (append-only, always positive) and summed for display.
Fainting or losing lives never removes points, skins or history.

## Levels and attributes

Owner decision, 2026-11-26. In the MVP attributes are **display only**; they will matter in the arena (Phase 3).

| Rule | Value |
| --- | --- |
| Experience | The points total (sum of `points_event`). No other source |
| Level threshold | 100 points per level *(tunable, starting value chosen by the coordinator, owner to confirm)*: level 1 at 0 points, level 2 at 100, level 3 at 200, ... (`level = points // 100 + 1`) |
| Never down | Points are append-only and never negative, so the level never goes down. Fainting or losing lives never removes levels or attributes |
| Attribute points | Reaching level N grants N points, so level L has granted `L*(L+1)/2` in total (level 1: 1, level 2: 3, level 3: 6). A new pet at level 1 has 1 point to spend |
| Attributes | `strength`, `speed`, `skill`, `endurance`, `intelligence` (UI: Força, Velocidade, Habilidade, Resistência, Inteligência). All start at 0 |
| Spending | The user chooses where each point goes, in positive whole amounts, never more than the unspent points (all or nothing). Spent points are permanent: no reset in the MVP |
| Event | `level_up` once when the level is higher than the last level returned to the client (several levels at once: one event) |
| Paying | Never grants levels, points or attributes |

The level is computed from points on read, never stored; only spent attributes and the last level seen by the
client are stored. Nothing here uses body data, calories or meal judgement.

## Limits

| Plan | AI photos per local day |
| --- | --- |
| Free | 2 |
| Premium | *(not decided yet — ask before implementing)* |

A failed analysis (unreadable photo, provider error, not food) does not consume the limit.
A manual entry (RF-95) never consumes the limit; it follows the same lives, streak and points rules as a photo log.

## Risk pattern (RF-98) — threshold not decided, disabled

*(tunable)* `risk_pattern_days = None` (**disabled**: the product owner has not chosen N). When set to N, `GET /v1/pet`
returns `support_hint: true` if the N completed local days before today all had no log, none was paused, and none
is before the pet's creation day; a log today clears it. It is a hint for a kind message and the CVV 188 path:
it never changes lives, streak or points, and never punishes. Do not enable it in production before N is decided.

## Required tests (minimum)

- Starts with 2 lives; never above 4; never below 0.
- One missed day → 1 life, mood `sleepy`. Two missed days → 0, `fainted`.
- Log while fainted → 1 life, `wake_up` event, +5 points.
- 7 consecutive days → +1 life and `celebrate`; at 4 lives no extra life.
- Pause covering missed days → no loss, streak kept.
- Day boundaries in `America/Sao_Paulo` and in a timezone with DST (e.g. `America/New_York`), including a log at 23:59 and 00:01.
- `settle` is idempotent (calling twice changes nothing).
- Hitting the daily AI limit never changes lives.
- Level 1 at 0 points with 1 attribute point; level thresholds every 100 points; several levels crossed in one log;
  level and attributes never decrease after fainting; spending more than unspent is rejected and changes nothing.
