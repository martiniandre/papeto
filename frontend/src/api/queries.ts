import { QueryClient, useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { isApiError } from './client';
import { api } from './endpoints';
import type { MealRange, Pet, PetUpdate } from './types';

export const queryKeys = {
  me: ['me'] as const,
  pet: ['pet'] as const,
  meals: (range: MealRange) => ['meals', range] as const,
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

export const usePet = (enabled = true) =>
  useQuery({ queryKey: queryKeys.pet, queryFn: api.getPet, enabled });

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
