# Screens and flows

Numbers match the design canvas (page Layout). The page Fluxo has the full arrow diagram:
https://claude.ai/artifact/1kwmN9FBtScfqXR6yRmJ2N

## Flows

1. **First access:** 1 Sign in (Apple, Google or email) → 2 Age and terms (two checkboxes: terms/privacy and meal-data consent; Continue only when both) → 43 Name your pet (pet hidden until it has a name, max 20 chars, 3 suggestions) → 24 Meet your pet (reveal + color) → 30 How lives work → 3 Home. Email: 21 Sign in with email → 22 Create account / 23 Recover password; existing account goes straight to Home.
2. **Log a meal:** 3 Home → 9 Camera permission (first use only) → 4 Camera (or gallery) → 5 Analyzing (Cancel returns to Camera) → 6 Result ("Sobre este prato" accordion open) → 31 Allow notifications (first meal only) → Home. AI failure → 10 Analysis error → retry. With 2/2 photos used, Home is 40 and Log opens 11 Daily limit.
3. **History:** 7 History (today, 7 days, 30 days) → 25 Meal detail → 37 Delete meal → 42 History with "Refeição apagada" + Undo. Empty: 14.
4. **Profile and account:** 8 Profile → 27 Notifications · 36 Export data · 35 Delete account (button enabled only after confirming) → 41 Account deleted → Sign in.
5. **Premium:** 15 Subscribe (X and "Agora não" close it) → 16 Premium active → 38 Home (subscriber) → 13 Pause (1, 3 or 7 days) → 39 Home paused → Resume. Entry points: Result ("Seus hábitos"), Daily limit, Pause button, Profile. Subscriber versions: 32 Result, 33 Profile, 34 Your subscription.
6. **Pet lives (shown when opening the app):** 28 Lost a life (day without a log) → 12 Fainted (0 lives) → a logged meal wakes the pet.
7. **Levels and attributes:** 3 Home shows the level, a progress bar to the next level (from `level_progress`) and an "Atributos" entry, highlighted (amber card, star, "N pontos para distribuir") when `unspent_attribute_points > 0` → 44 Attributes (`/attributes`) → back to Home. A `level_up` event shows a small "Subiu para o nível N!" chip on Home and the celebrating pet art (static with reduced motion; also on 6 Result).

Additions (privacy, safety, manual entry, offline):

- **Manual entry (RF-95):** 10 Analysis error → "Escolher os alimentos" → Manual entry (`/meal/manual`: meal type + foods, `POST /v1/meals/manual`) → 6 Result. It never mentions the photo limit.
- **Offline queue:** if the photo request cannot reach the server (or the device is offline), screen 10 shows "Sem conexão", keeps the pending photo in memory only and sends it when the connection returns. If the app is killed the pending photo is lost by design.
- **Profile > Privacidade** (`/account/privacy`): revoke the meal-data consent (explains the effect first, offers export and "Apagar meus registros de refeição"), analytics switch, links to Terms and Privacy Policy (placeholder URLs from `src/config.ts`).
- **Profile > Apoio** (`/account/support`): notice that the app does not replace a doctor or nutritionist, and CVV 188 (`tel:188`, https://cvv.org.br). Home shows a discreet card with the same path when `GET /pet` returns `support_hint=true`.
- **Reset password** (`/reset-password?token=...`, deep link `papeto://reset-password?token=...`): new password with `POST /v1/auth/password/reset`; an invalid or expired token offers a new link (23).

Correct meal (26) returns to the screen it was opened from (Result or Meal detail).

## States every data screen handles

Loading (skeleton), offline banner ("Sem conexão. Tentamos de novo quando voltar."), server error with "Tentar de novo",
large system font, screen reader.

| Screen | States |
| --- | --- |
| 1 Sign in | default; signing in (tapped button shows progress, others disabled); failure message; new account → 2; existing → 3 |
| 21 Email sign in | empty (button disabled); filled; password shown/hidden; invalid email; wrong password; too many attempts; signing in |
| 22 Create account | empty; weak password (rules under the field); email already registered (link to sign in); creating |
| 23 Recover password | empty; sent — same message whether or not the email exists |
| 2 Age and terms | none checked; one checked; both checked (Continue enabled) |
| 43 Name your pet | empty (button disabled); filled; suggestion tapped; 20-char limit |
| 24 Meet your pet | reveal with the chosen name; color selected |
| 3 Home | level and progress; attributes entry with and without unspent points; level up; happy; tired; sleepy; fainted; paused; photos used up; first day without meals; subscriber |
| 44 Attributes | loading; error with retry; offline (banner, and "Sem conexão" on confirm); no points to spend (steppers disabled, short message); allocating (+/- per attribute, remaining count never below 0, confirm disabled until something is allocated); confirming (explains that spent points are permanent, "Confirmar" / "Voltar e revisar"); saving; success ("Pontos distribuídos!"); points changed (`NOT_ENOUGH_ATTRIBUTE_POINTS`: refetch the pet, clear the draft, show "Seus pontos mudaram") |
| 9 Camera permission | first request; denied before ("Abrir Ajustes"); gallery only |
| 4 Camera | live; flash on/off; low light hint; no camera (opens gallery) |
| 5 Analyzing | analyzing; slow (> 10 s, "Ainda olhando…"); cancelled |
| 10 Analysis error | not food; dark or blurry; offline; AI error — each with its own text; does not count toward the limit |
| 6 Result | accordion open/closed; low confidence (ask to check items); first meal (→ 31); pet woke up or gained a life (celebrate); subscriber |
| 11 Daily limit | 2 of 2 used; resets at local midnight |
| 26 Correct meal | editing; item removed; item added; saving; save error |
| 7 History | today / 7 days / 30 days; empty; after delete (Undo for 5 s) |
| 25 Meal detail | free; subscriber; corrected by you (badge) |
| 27 Notifications | on; off; denied by the system (link to Settings) |
| 31 Allow notifications | first request; "Agora não" (do not ask again for 7 days) |
| 13 Pause | 1, 3 or 7 days; not Premium (opens 15) |
| 15 Subscribe | yearly or monthly; processing; card declined; Pix awaiting payment; done (16) |
| 34 Your subscription | active; cancelled but valid until period end; payment overdue |
| 17 Consistency dashboard | fewer than 3 days of logs; with data |
| 35 Delete account | confirmation unchecked (button disabled); checked; deleting; done (41) |
| 36 Export data | ready; preparing; sent by email |

## Accessibility (from the 25/11 audit)

Text contrast AA; input borders and empty hearts at least 3:1 (`#7D839A`); touch targets >= 44; no fixed heights on
buttons, chips or inputs (use min-height); badges at least 12 px; labels on icon buttons; selected states not by color
only (check icon + "selected"); current tab announced; analysis progress announced; locked "Seus hábitos" announced
as locked; respect reduced motion (static image of the mood).
