import { useQueryClient } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useCallback } from 'react';

import { api } from '@/api/endpoints';
import { queryKeys } from '@/api/queries';
import type { LoginInput, RegisterInput } from '@/api/types';
import { nextOnboardingRoute } from '@/features/onboarding/nextRoute';

import { startSession } from './session';

export function useAuthActions() {
  const queryClient = useQueryClient();

  /** Existing account: consents and pet decide the next screen (flow 1). */
  const goAfterSignIn = useCallback(async () => {
    const [me, pet] = await Promise.all([
      queryClient.fetchQuery({ queryKey: queryKeys.me, queryFn: api.getMe }),
      queryClient.fetchQuery({ queryKey: queryKeys.pet, queryFn: api.getPet }),
    ]);
    router.replace(nextOnboardingRoute(me, pet));
  }, [queryClient]);

  const signIn = useCallback(
    async (input: LoginInput) => {
      await startSession(await api.login(input));
      await goAfterSignIn();
    },
    [goAfterSignIn],
  );

  /** New account → 2 Age and terms. */
  const register = useCallback(async (input: RegisterInput) => {
    await startSession(await api.register(input));
    router.replace('/(onboarding)/age-terms');
  }, []);

  return { signIn, register, goAfterSignIn };
}
