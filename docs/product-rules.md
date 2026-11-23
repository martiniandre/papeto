# Product, safety and privacy rules

Distilled from the scope doc and the legal draft (Terms of Use and Privacy Policy, v1.0, not yet reviewed by a lawyer).
These are requirements for the code, not legal text.

## Safety (food)

- The app describes the plate; it never judges it. No score, no "healthy/unhealthy", no negative points.
- No calories, macros, portions in grams, weight, height or body data in the MVP. (RF-94, optional calories, is out of scope.)
- Portions, if shown, are labeled as an estimate and editable.
- If the photo is not food or cannot be read: friendly error, tips, retry or gallery; the attempt does not count toward the daily limit.
- Risk pattern (for example many days in a row without logs): a warm message and a discreet support path, never punishment. Support text links to CVV 188.
- Copy tone: short and kind. Never guilt, never mention body, weight or calories.

## Age and consent

- 18+ confirmation at sign-up (plus the store age signal when available).
- Two separate consents, stored in `consent` with document, version and timestamp:
  - `terms_privacy` — Terms of Use and Privacy Policy;
  - `meal_data` — specific, highlighted consent for meal photos and meal records (LGPD art. 11, I).
- Without an active `meal_data` consent, meal endpoints return 403 `MEAL_CONSENT_REQUIRED`.
- Revoking `meal_data` (Profile > Privacy): stop analyzing photos and offer export + delete of meal records or the account.
- Analytics can be turned off in Profile > Privacy (stored per user, respected by `AnalyticsProvider`).

## Data handling

| Data | Retention |
| --- | --- |
| Meal photos | Never stored. Discarded right after analysis (seconds). |
| Meal records, pet, points | While the account exists |
| Consent records | While the account exists + 5 years |
| Subscription and receipts | 5 years (tax) |
| Support messages | 2 years after the last message |
| Usage analytics and errors | Up to 12 months, random id only (no name, no email) |

- The vision provider receives only the resized image, no name or email.
- Account deletion: pending for 30 days (user can come back by signing in), then hard delete or anonymize what the law requires to keep.
- Export (`GET /v1/me/export`): JSON with everything about the user. Always free.
- Privacy requests answered within 15 days.

## Payments and Premium

- Premium is a monthly or yearly subscription (Stripe on the web, store billing in the apps). Prices are not decided: use placeholders.
- Pix payments are valid for the paid period and do not auto-renew; remind the user before it ends.
- Price changes: 30 days notice, effective at the next renewal.
- Failed payment: retry for a few days, then downgrade to Free without losing pet, points or history.
- Web purchases: 7-day full refund (CDC art. 49). Store purchases follow store policy.
- Paying never gives the pet power in any competition. Keeping the pet alive never requires paying.

## Vendors (must match the Privacy Policy table)

Fly.io (Brazil, São Paulo) · Upstash (Brazil, São Paulo) · vision provider (TBD) · Expo push (US) · Stripe (US) ·
Apple and Google (US) · Sentry (US) · PostHog (US). Adding a vendor means updating the Privacy Policy.
