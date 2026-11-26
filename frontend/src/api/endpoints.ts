import { request } from './client';
import type {
  ConsentInput,
  DataExport,
  LoginInput,
  Me,
  Meal,
  MealCreated,
  MealPatch,
  MealPage,
  MealRange,
  Pet,
  PetUpdate,
  RegisterInput,
  TokenPair,
} from './types';

/** One function per endpoint in docs/api.md used by flows 1 and 2 and the tabs. */
export const api = {
  register: (input: RegisterInput) =>
    request<TokenPair>('/auth/register', { method: 'POST', body: input, anonymous: true }),
  login: (input: LoginInput) =>
    request<TokenPair>('/auth/login', { method: 'POST', body: input, anonymous: true }),
  /** TODO(backend): POST /v1/auth/password/forgot is not in the OpenAPI yet; this call will 404. */
  forgotPassword: (email: string) =>
    request<void>('/auth/password/forgot', { method: 'POST', body: { email }, anonymous: true }),

  acceptConsent: (input: ConsentInput) =>
    request<void>('/consents', { method: 'POST', body: input }),
  getMe: () => request<Me>('/me'),
  /** Starts the 30-day pending deletion (202 `{deletion_scheduled_for}`). Never needs consent. */
  deleteAccount: () => request<{ deletion_scheduled_for: string }>('/me', { method: 'DELETE' }),
  /** Everything about the user as JSON. Always free. */
  exportData: () => request<DataExport>('/me/export'),

  getPet: () => request<Pet>('/pet'),
  updatePet: (input: PetUpdate) => request<Pet>('/pet', { method: 'PATCH', body: input }),

  /** `photo` must already be resized (see features/meal/resizePhoto). */
  createMeal: (photoUri: string, signal?: AbortSignal) => {
    const form = new FormData();
    // React Native's FormData accepts a file descriptor object.
    form.append('photo', { uri: photoUri, name: 'meal.jpg', type: 'image/jpeg' } as unknown as Blob);
    return request<MealCreated>('/meals', { method: 'POST', body: form, signal });
  },
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
