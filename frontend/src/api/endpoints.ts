import { request } from './client';
import type {
  ConsentInput,
  LoginInput,
  Me,
  MealCreated,
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

  getPet: () => request<Pet>('/pet'),
  updatePet: (input: PetUpdate) => request<Pet>('/pet', { method: 'PATCH', body: input }),

  /** `photo` must already be resized (see features/meal/resizePhoto). */
  createMeal: (photoUri: string, signal?: AbortSignal) => {
    const form = new FormData();
    // React Native's FormData accepts a file descriptor object.
    form.append('photo', { uri: photoUri, name: 'meal.jpg', type: 'image/jpeg' } as unknown as Blob);
    return request<MealCreated>('/meals', { method: 'POST', body: form, signal });
  },
  listMeals: (range: MealRange, cursor?: string) =>
    request<MealPage>('/meals', { query: { range, cursor } }),
};
