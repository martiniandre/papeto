import { useMutation, useQueryClient } from '@tanstack/react-query';

import { api } from '@/api/endpoints';
import { queryKeys, useUpdateMe } from '@/api/queries';
import type { ConsentType, Me } from '@/api/types';
import { CONSENT_VERSION } from '@/features/onboarding/nextRoute';

/** The latest record of a consent type decides (the API keeps the history). */
export function isConsentActive(me: Pick<Me, 'consents'>, type: ConsentType): boolean {
  const records = me.consents.filter((consent) => consent.type === type);
  if (records.length === 0) return false;
  const latest = records.reduce((a, b) => (a.recorded_at >= b.recorded_at ? a : b));
  return latest.accepted;
}

/**
 * Profile > Privacidade. The two calls below are the ones the backend worker is adding
 * (consent revoke via POST /consents `accepted:false`, DELETE /meals); keep them here so they are easy to adjust.
 */
export function usePrivacyActions() {
  const client = useQueryClient();
  const updateMe = useUpdateMe();

  const setMealConsent = useMutation({
    mutationFn: (accepted: boolean) =>
      api.acceptConsent({ type: 'meal_data', version: CONSENT_VERSION, accepted }),
    onSuccess: () => client.invalidateQueries({ queryKey: queryKeys.me }),
  });

  const deleteMeals = useMutation({
    mutationFn: () => api.deleteAllMeals(),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: queryKeys.mealsAll });
      void client.invalidateQueries({ queryKey: ['meal'] });
    },
  });

  return {
    setMealConsent,
    deleteMeals,
    setAnalytics: (enabled: boolean) => updateMe.mutate({ analytics_opt_out: !enabled }),
    analyticsSaving: updateMe.isPending,
    analyticsFailed: updateMe.isError,
  };
}
