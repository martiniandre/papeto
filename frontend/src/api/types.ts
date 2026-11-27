/**
 * API types, derived from the backend OpenAPI (`npm run api:types` -> schema.gen.ts).
 * Do not hand-write response shapes here: alias the generated schemas so they stay in sync.
 */
import type { components } from './schema.gen';

type Schemas = components['schemas'];

export type Mood = Schemas['Mood'];
export const MOODS: readonly Mood[] = ['happy', 'tired', 'sleepy', 'fainted', 'paused'];

export type PetEvent = Schemas['PetEvent'];

export type Attributes = Schemas['AttributesOut'];
export type AttributeName = keyof Attributes;
/** Display order of the five attributes (names only; the numbers always come from the API). */
export const ATTRIBUTE_NAMES: readonly AttributeName[] = [
  'strength',
  'speed',
  'skill',
  'endurance',
  'intelligence',
];
export type LevelProgress = Schemas['LevelProgressOut'];
/** POST /pet/attributes body: positive whole amounts per attribute. */
export type AttributeAllocations = Partial<Record<AttributeName, number>>;

/**
 * The backend stores the color as a free key (`^[a-z0-9_-]{1,20}$`) and starts every pet with
 * "default". The app offers PET_COLORS and falls back to a neutral halo for unknown keys.
 */
export type PetColor = string;
export const PET_COLORS = ['lilac', 'mint', 'peach', 'sky'] as const;
export type OfferedPetColor = (typeof PET_COLORS)[number];

/**
 * GET /pet. A new pet has `name: null` until the user names it (screen 43). `support_hint` flags the RF-98
 * risk pattern (always false while the server threshold is unset); both come from the generated schema.
 */
export type Pet = Schemas['PetResponse'];
/** Pet summary returned inside a logged meal (no events). */
export type PetSummary = Schemas['PetSummary'];
export type PetUpdate = { name?: string; color?: PetColor };

export type ConsentType = Schemas['ConsentType'];
export type ConsentInput = Schemas['ConsentRequest'];
export type ConsentRecord = Schemas['ConsentOut'];

export type DataExport = Schemas['ExportResponse'];

export type Plan = Schemas['Plan'];
export type Me = Schemas['MeResponse'];
export type MeUpdate = Schemas['MePatch'];
export type NotificationPrefs = Schemas['NotificationsOut'];
export type NotificationPrefsPatch = Schemas['NotificationsPatch'];
export type PushTokenInput = Schemas['PushTokenRequest'];
export type ManualMealInput = Schemas['ManualMealRequest'];

export type TokenResponse = Schemas['TokenResponse'];
/** The part of the token response the app persists. */
export type TokenPair = Pick<TokenResponse, 'access_token' | 'refresh_token'>;
export type GoogleSignInInput = Schemas['GoogleSignInRequest'];
export type GoogleTokenResponse = Schemas['GoogleSignInResponse'];
export type RegisterInput = Schemas['RegisterRequest'];
export type LoginInput = Schemas['LoginRequest'];

export type MealType = Schemas['MealType'];
/** `plate_share` and `new_foods` are empty for free users (Premium view fills them). */
export type Meal = Schemas['MealOut'];
export type MealCreated = Schemas['LogMealResponse'];
export type MealPatch = Schemas['MealPatch'];
export type MealRange = Schemas['MealRange'];
export type MealPage = Schemas['MealListResponse'];

/** Stable error codes from be/app/api/errors.py. Unknown codes are still allowed. */
export type ApiErrorCode =
  | 'UNAUTHORIZED'
  | 'INVALID_TOKEN'
  | 'INVALID_CREDENTIALS'
  | 'EMAIL_ALREADY_REGISTERED'
  | 'ADULT_CONFIRMATION_REQUIRED'
  | 'GOOGLE_TOKEN_INVALID'
  | 'GOOGLE_EMAIL_NOT_VERIFIED'
  | 'AUTH_PROVIDER_UNAVAILABLE'
  | 'INVALID_TIMEZONE'
  | 'VALIDATION_ERROR'
  | 'MEAL_CONSENT_REQUIRED'
  | 'DAILY_LIMIT_REACHED'
  | 'PHOTO_NOT_READABLE'
  | 'PHOTO_TOO_LARGE'
  | 'NOT_FOOD'
  | 'VISION_UNAVAILABLE'
  | 'PREMIUM_REQUIRED'
  | 'MEAL_NOT_FOUND'
  | 'PET_NOT_FOUND'
  | 'PET_ALREADY_PAUSED'
  | 'PET_NOT_PAUSED'
  | 'NOT_ENOUGH_ATTRIBUTE_POINTS'
  | 'INVALID_CURSOR'
  | 'INVALID_RESET_TOKEN'
  | 'NOT_FOUND'
  | 'METHOD_NOT_ALLOWED'
  | 'INTERNAL_ERROR'
  | (string & {});

export interface ApiErrorBody {
  error: { code: ApiErrorCode; message: string };
}
