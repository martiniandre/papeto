/**
 * Hand-written API types matching docs/api.md (v1).
 *
 * The backend OpenAPI is not available yet. Once it is, run `npm run api:types`
 * (writes src/api/schema.gen.ts) and replace these aliases with the generated
 * `components['schemas'][...]` types. Shapes marked ASSUMPTION are not spelled
 * out in docs/api.md and must be checked against the real OpenAPI.
 */

export type Mood = 'happy' | 'tired' | 'sleepy' | 'fainted' | 'paused';
export const MOODS: readonly Mood[] = ['happy', 'tired', 'sleepy', 'fainted', 'paused'];

export type PetEvent = 'wake_up' | 'life_lost' | 'celebrate';

/** ASSUMPTION: the color vocabulary is not defined in docs; the app offers these keys. */
export type PetColor = 'lilac' | 'mint' | 'peach' | 'sky';
export const PET_COLORS: readonly PetColor[] = ['lilac', 'mint', 'peach', 'sky'];

export interface Pet {
  /** null until the user names the pet (screen 43). ASSUMPTION: nullable. */
  name: string | null;
  color: PetColor | null;
  lives: number;
  max_lives: number;
  streak_days: number;
  points: number;
  mood: Mood;
  events: PetEvent[];
}

export interface PetUpdate {
  name?: string;
  color?: PetColor;
}

export type ConsentType = 'terms_privacy' | 'meal_data' | 'analytics';

export interface ConsentInput {
  type: ConsentType;
  version: string;
  accepted: boolean;
}

/** ASSUMPTION: shape of a consent inside GET /me. */
export interface ConsentRecord {
  type: ConsentType;
  version: string;
  accepted: boolean;
  accepted_at: string | null;
}

export type Plan = 'free' | 'premium';

/** ASSUMPTION: docs/api.md only says "profile, plan, consents, timezone". */
export interface Me {
  id: string;
  name: string;
  email: string;
  plan: Plan;
  timezone: string;
  analytics_opt_out: boolean;
  consents: ConsentRecord[];
}

/** ASSUMPTION: token pair returned by register, login, social and refresh. */
export interface TokenPair {
  access_token: string;
  refresh_token: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  name: string;
  /** The backend rejects the request unless this is true (422 ADULT_CONFIRMATION_REQUIRED). */
  adult_confirmed: boolean;
  /** IANA timezone; the backend defaults to America/Sao_Paulo. */
  timezone?: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';

/** Vision result fields (docs/api.md) plus record fields (ASSUMPTION: id, created_at, corrected). */
export interface Meal {
  id: string;
  created_at: string;
  description: string;
  items: string[];
  meal_type: MealType;
  food_groups: string[];
  item_count: number;
  colors: string[];
  confidence: number;
  corrected: boolean;
  /** Premium view only. */
  plate_share?: Record<string, number> | null;
  /** Premium view only. */
  new_foods?: string[] | null;
}

export interface MealCreated {
  meal: Meal;
  pet: Pet;
  events: PetEvent[];
}

export type MealRange = 'today' | '7d' | '30d';

/** ASSUMPTION: cursor page shape for GET /meals. */
export interface MealPage {
  items: Meal[];
  next_cursor: string | null;
}

export type ApiErrorCode =
  | 'MEAL_CONSENT_REQUIRED'
  | 'DAILY_LIMIT_REACHED'
  | 'PHOTO_NOT_READABLE'
  | 'NOT_FOOD'
  | 'VISION_UNAVAILABLE'
  | 'PREMIUM_REQUIRED'
  | 'INVALID_CREDENTIALS'
  | 'EMAIL_ALREADY_REGISTERED'
  | 'TOO_MANY_ATTEMPTS'
  | 'UNAUTHORIZED'
  | (string & {});

export interface ApiErrorBody {
  error: { code: ApiErrorCode; message: string };
}
