import { useMutation, useQueryClient } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { isApiError } from '@/api/client';
import { api } from '@/api/endpoints';
import { queryKeys } from '@/api/queries';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Checkbox } from '@/components/ui/Checkbox';
import { Text } from '@/components/ui/Text';
import { errorMessage } from '@/i18n';

import { CONSENT_VERSION } from './nextRoute';

/** Screen 2: two separate consents (terms/privacy + 18+, and meal data). Continue only when both. */
export default function AgeTermsScreen() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [terms, setTerms] = useState(false);
  const [mealData, setMealData] = useState(false);
  const both = terms && mealData;

  const save = useMutation({
    mutationFn: async () => {
      // Adult confirmation first: consents and pet endpoints refuse an unconfirmed adult.
      await api.updateMe({ adult_confirmed: true });
      await api.acceptConsent({ type: 'terms_privacy', version: CONSENT_VERSION, accepted: true });
      await api.acceptConsent({ type: 'meal_data', version: CONSENT_VERSION, accepted: true });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.me });
      // An existing pet name (account that came back) skips naming.
      const pet = await queryClient.fetchQuery({ queryKey: queryKeys.pet, queryFn: api.getPet });
      router.replace(pet.name ? '/(tabs)/home' : '/(onboarding)/name-pet');
    },
  });

  return (
    <Screen
      footer={
        <>
          {!both ? (
            <Text variant="secondary" className="text-center">
              {t('onboarding.terms.bothRequired')}
            </Text>
          ) : null}
          <Button
            testID="terms-continue"
            label={save.isPending ? t('onboarding.terms.saving') : t('common.continue')}
            disabled={!both}
            loading={save.isPending}
            onPress={() => save.mutate()}
          />
        </>
      }
    >
      <Text variant="title">{t('onboarding.terms.title')}</Text>
      <Text variant="secondary">{t('onboarding.terms.body')}</Text>
      <Checkbox
        testID="consent-terms"
        label={t('onboarding.terms.termsCheckbox')}
        checked={terms}
        onChange={setTerms}
      />
      <View className="gap-sm">
        <Text variant="subtitle">{t('onboarding.terms.mealDataTitle')}</Text>
        <Checkbox
          testID="consent-meal-data"
          emphasized
          label={t('onboarding.terms.mealDataCheckbox')}
          checked={mealData}
          onChange={setMealData}
        />
      </View>
      {save.isError ? (
        <Text accessibilityRole="alert" className="font-semibold">
          {isApiError(save.error) ? errorMessage(save.error.code) : t('common.serverError')}
        </Text>
      ) : null}
    </Screen>
  );
}
