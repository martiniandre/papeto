import { useQueryClient } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useCallback } from 'react';

import { api } from '@/api/endpoints';
import { queryKeys } from '@/api/queries';
import type { LoginInput, RegisterInput } from '@/api/types';
import { hasRequiredConsents, nextOnboardingRoute } from '@/features/onboarding/nextRoute';

import { startSession } from './session';

export function useAuthActions() {
  const queryClient = useQueryClient();

  /** Existing account: consents and pet decide the next screen (flow 1). */
  const goAfterSignIn = useCallback(async () => {
    const me = await queryClient.fetchQuery({ queryKey: queryKeys.me, queryFn: api.getMe });
    // GET /pet answers 403 until the adult is confirmed, so ask for it only afterwards.
    if (!me.adult_confirmed || !hasRequiredConsents(me)) {
      router.replace('/(onboarding)/age-terms');
      return;
    }
    const pet = await queryClient.fetchQuery({ queryKey: queryKeys.pet, queryFn: api.getPet });
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

  /** Google: new account → 2 Age and terms; existing account → whatever step is still missing. */
  const signInWithGoogle = useCallback(
    async (idToken: string) => {
      const response = await api.googleSignIn({
        id_token: idToken,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      });
      await startSession(response);
      if (response.is_new_user) {
        router.replace('/(onboarding)/age-terms');
        return;
      }
      await goAfterSignIn();
    },
    [goAfterSignIn],
  );

  return { signIn, register, signInWithGoogle, goAfterSignIn };
}
