import { QueryClient, useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { isApiError } from './client';
import { usePetAlertStore } from '@/stores/petAlerts';

import { api } from './endpoints';
import type { Meal, MealPatch, MealRange, Pet, PetUpdate } from './types';

export const queryKeys = {
  me: ['me'] as const,
  pet: ['pet'] as const,
  meals: (range: MealRange) => ['meals', range] as const,
  mealsAll: ['meals'] as const,
  meal: (id: string) => ['meal', id] as const,
};

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: (failureCount, error) =>
          failureCount < 2 && !(isApiError(error) && error.status >= 400 && error.status < 500),
      },
      mutations: { retry: false },
    },
  });
}

export const useMe = (enabled = true) => useQuery({ queryKey: queryKeys.me, queryFn: api.getMe, enabled });

/** `life_lost` is returned once by the API, so it is remembered here before the next refetch replaces it. */
async function fetchPet(): Promise<Pet> {
  const pet = await api.getPet();
  if (pet.events.includes('life_lost')) usePetAlertStore.getState().noteLifeLost();
  return pet;
}

export const usePet = (enabled = true) =>
  useQuery({ queryKey: queryKeys.pet, queryFn: fetchPet, enabled });

export function useUpdatePet() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: PetUpdate) => api.updatePet(input),
    onSuccess: (pet: Pet) => client.setQueryData(queryKeys.pet, pet),
  });
}

export const useMeals = (range: MealRange) =>
  useInfiniteQuery({
    queryKey: queryKeys.meals(range),
    queryFn: ({ pageParam }) => api.listMeals(range, pageParam),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last) => last.next_cursor ?? undefined,
  });

export const useMeal = (id: string) =>
  useQuery({ queryKey: queryKeys.meal(id), queryFn: () => api.getMeal(id) });

/** PATCH /meals/{id}. Points never change, so the pet is not refetched. */
export function useUpdateMeal(id: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: MealPatch) => api.updateMeal(id, input),
    onSuccess: (meal: Meal) => {
      client.setQueryData(queryKeys.meal(id), meal);
      void client.invalidateQueries({ queryKey: queryKeys.mealsAll });
    },
  });
}
