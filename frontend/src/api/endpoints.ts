import { request } from './client';
import type {
  ConsentInput,
  DataExport,
  LoginInput,
  Me,
  Meal,
  MealCreated,
  ManualMealInput,
  MealPatch,
  MealPage,
  MealRange,
  MeUpdate,
  AttributeAllocations,
  Pet,
  PetUpdate,
  PushTokenInput,
  RegisterInput,
  TokenPair,
} from './types';

/** One function per endpoint in docs/api.md used by flows 1 and 2 and the tabs. */
export const api = {
  register: (input: RegisterInput) =>
    request<TokenPair>('/auth/register', { method: 'POST', body: input, anonymous: true }),
  login: (input: LoginInput) =>
    request<TokenPair>('/auth/login', { method: 'POST', body: input, anonymous: true }),
  /** Always 202 `{status: "accepted"}`, whether or not the email has an account. */
  forgotPassword: (email: string) =>
    request<{ status: string }>('/auth/password/forgot', {
      method: 'POST',
      body: { email },
      anonymous: true,
    }),
  /** 204; 400 `INVALID_RESET_TOKEN` when the token is unknown, used or expired. */
  resetPassword: (token: string, password: string) =>
    request<void>('/auth/password/reset', {
      method: 'POST',
      body: { token, password },
      anonymous: true,
    }),

  acceptConsent: (input: ConsentInput) =>
    request<void>('/consents', { method: 'POST', body: input }),
  getMe: () => request<Me>('/me'),
  /** Partial update: timezone, analytics opt-out, `notifications` (any subset). */
  updateMe: (input: MeUpdate) => request<Me>('/me', { method: 'PATCH', body: input }),
  /** Starts the 30-day pending deletion (202 `{deletion_scheduled_for}`). Never needs consent. */
  deleteAccount: () => request<{ deletion_scheduled_for: string }>('/me', { method: 'DELETE' }),
  /** Everything about the user as JSON. Always free. */
  exportData: () => request<DataExport>('/me/export'),

  getPet: () => request<Pet>('/pet'),
  updatePet: (input: PetUpdate) => request<Pet>('/pet', { method: 'PATCH', body: input }),
  /** Spends unspent attribute points for good (no reset). 400 `NOT_ENOUGH_ATTRIBUTE_POINTS` spends nothing. */
  spendAttributes: (allocations: AttributeAllocations) =>
    request<Pet>('/pet/attributes', { method: 'POST', body: { allocations } }),

  /** `photo` must already be resized (see features/meal/resizePhoto). */
  createMeal: (photoUri: string, signal?: AbortSignal) => {
    const form = new FormData();
    // React Native's FormData accepts a file descriptor object.
    form.append('photo', { uri: photoUri, name: 'meal.jpg', type: 'image/jpeg' } as unknown as Blob);
    return request<MealCreated>('/meals', { method: 'POST', body: form, signal });
  },
  /** RF-95: items and meal type chosen by hand. Never calls the vision provider or uses the photo limit. */
  createManualMeal: (input: ManualMealInput) =>
    request<MealCreated>('/meals/manual', { method: 'POST', body: input }),
  /**
   * Deletes every meal record (account and pet stay). Consent revoke and delete-all are kept behind
   * these two functions because the backend worker is still adding them.
   */
  deleteAllMeals: () => request<void>('/meals', { method: 'DELETE' }),
  /** Registers or refreshes an Expo push token. Needs no meal consent. */
  registerPushToken: (input: PushTokenInput) =>
    request<PushTokenInput>('/push-tokens', { method: 'POST', body: input }),
  deletePushToken: (token: string) =>
    request<void>(`/push-tokens/${encodeURIComponent(token)}`, { method: 'DELETE' }),
  getMeal: (id: string) => request<Meal>(`/meals/${encodeURIComponent(id)}`),
  /** Corrects items and meal type. Points never change. */
  updateMeal: (id: string, input: MealPatch) =>
    request<Meal>(`/meals/${encodeURIComponent(id)}`, { method: 'PATCH', body: input }),
  /** Soft delete. The 5 s undo is client-side (see features/history/pendingDelete). */
  deleteMeal: (id: string) =>
    request<void>(`/meals/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  listMeals: (range: MealRange, cursor?: string) =>
    request<MealPage>('/meals', { query: { range, cursor } }),
};
