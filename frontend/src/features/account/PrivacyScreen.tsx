import { router } from 'expo-router';
import { useState } from 'react';
import { Linking, Pressable, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { useMe } from '@/api/queries';
import { ErrorState } from '@/components/ErrorState';
import { Screen } from '@/components/Screen';
import { Skeleton } from '@/components/Skeleton';
import { Button } from '@/components/ui/Button';
import { Icon, type IconName } from '@/components/ui/Icon';
import { IconButton } from '@/components/ui/IconButton';
import { Text } from '@/components/ui/Text';
import { ToggleRow } from '@/components/ui/ToggleRow';
import { PRIVACY_URL, TERMS_URL } from '@/config';
import { colors } from '@/theme/tokens';

import { isConsentActive, usePrivacyActions } from './usePrivacy';

type Step = 'idle' | 'revoke' | 'delete';

function LinkRow({ testID, icon, label, url }: { testID: string; icon: IconName; label: string; url: string }) {
  return (
    <Pressable
      testID={testID}
      accessibilityRole="link"
      accessibilityLabel={label}
      onPress={() => void Linking.openURL(url)}
      className="min-h-touch flex-row items-center gap-md px-lg py-sm"
    >
      <Icon name={icon} color={colors.text} />
      <Text className="flex-1 font-semibold">{label}</Text>
      <Icon name="open-outline" color={colors.textSecondary} />
    </Pressable>
  );
}

/**
 * Profile > Privacidade: meal-data consent (revoke with explanation, export, delete meal records),
 * analytics switch, links to the Terms and the Privacy Policy.
 */
export default function PrivacyScreen() {
  const { t } = useTranslation();
  const me = useMe();
  const { setMealConsent, deleteMeals, setAnalytics, analyticsSaving, analyticsFailed } = usePrivacyActions();
  const [step, setStep] = useState<Step>('idle');

  const header = (
    <View className="flex-row items-center gap-sm">
      <IconButton icon="chevron-back" accessibilityLabel={t('common.back')} onPress={() => router.back()} />
      <Text variant="title" className="flex-1">
        {t('account.privacy.title')}
      </Text>
    </View>
  );

  if (me.isPending) {
    return (
      <Screen>
        {header}
        <Skeleton lines={4} />
      </Screen>
    );
  }
  if (me.isError) {
    return (
      <Screen>
        {header}
        <ErrorState error={me.error} onRetry={() => void me.refetch()} />
      </Screen>
    );
  }

  const mealConsent = isConsentActive(me.data, 'meal_data');
  const analyticsOn = !me.data.analytics_opt_out;
  const revoked = setMealConsent.isSuccess && !mealConsent;

  return (
    <Screen>
      {header}

      <View className="gap-sm rounded-lg bg-surface p-lg">
        <Text variant="subtitle">{t('account.privacy.mealTitle')}</Text>
        <Text
          testID="meal-consent-status"
          className="self-start rounded-pill bg-points-bg px-md py-xs font-semibold text-points-text"
        >
          {mealConsent ? t('account.privacy.mealOn') : t('account.privacy.mealOff')}
        </Text>
        <Text variant="secondary">{t('account.privacy.mealBody')}</Text>

        {mealConsent && step === 'idle' ? (
          <Button
            testID="revoke-start"
            action="secondary"
            label={t('account.privacy.revoke')}
            onPress={() => setStep('revoke')}
          />
        ) : null}
        {!mealConsent ? (
          <Button
            testID="consent-restore"
            action="secondary"
            label={t('account.privacy.allowAgain')}
            loading={setMealConsent.isPending}
            onPress={() => setMealConsent.mutate(true)}
          />
        ) : null}
      </View>

      {step === 'revoke' && mealConsent ? (
        <View testID="revoke-explain" className="gap-sm rounded-lg bg-points-bg p-lg">
          <Text className="font-heading text-points-text">{t('account.privacy.revokeTitle')}</Text>
          <Text className="text-points-text">{t('account.privacy.revokeEffect')}</Text>
          <Text className="text-points-text">{t('account.privacy.revokeKeeps')}</Text>
          <Button
            testID="revoke-confirm"
            action="danger"
            label={t('account.privacy.revokeConfirm')}
            loading={setMealConsent.isPending}
            onPress={() => setMealConsent.mutate(false, { onSuccess: () => setStep('idle') })}
          />
          <Button
            action="ghost"
            label={t('account.privacy.revokeKeep')}
            onPress={() => setStep('idle')}
          />
        </View>
      ) : null}

      {revoked ? (
        <Text testID="revoked-note" accessibilityRole="alert" className="font-semibold">
          {t('account.privacy.revoked')}
        </Text>
      ) : null}
      {setMealConsent.isError ? (
        <Text accessibilityRole="alert" className="font-semibold">
          {t('account.privacy.saveError')}
        </Text>
      ) : null}

      <View className="gap-sm rounded-lg bg-surface p-lg">
        <Text variant="subtitle">{t('account.privacy.yourRecords')}</Text>
        <Text variant="secondary">{t('account.privacy.recordsBody')}</Text>
        <Button
          testID="privacy-export"
          action="secondary"
          label={t('profile.export')}
          icon={<Icon name="download-outline" color={colors.primary} />}
          onPress={() => router.push('/account/export')}
        />
        {step !== 'delete' ? (
          <Button
            testID="delete-meals-start"
            action="secondary"
            label={t('account.privacy.deleteMeals')}
            onPress={() => setStep('delete')}
          />
        ) : (
          <View testID="delete-meals-confirm" className="gap-sm rounded-md bg-points-bg p-md">
            <Text className="font-heading text-points-text">{t('account.privacy.deleteMealsTitle')}</Text>
            <Text className="text-points-text">{t('account.privacy.deleteMealsBody')}</Text>
            <Button
              testID="delete-meals-confirm-button"
              action="danger"
              label={t('account.privacy.deleteMealsConfirm')}
              loading={deleteMeals.isPending}
              onPress={() => deleteMeals.mutate(undefined, { onSuccess: () => setStep('idle') })}
            />
            <Button action="ghost" label={t('common.cancel')} onPress={() => setStep('idle')} />
          </View>
        )}
        {deleteMeals.isSuccess && step === 'idle' ? (
          <Text testID="meals-deleted-note" accessibilityRole="alert" className="font-semibold">
            {t('account.privacy.mealsDeleted')}
          </Text>
        ) : null}
        {deleteMeals.isError ? (
          <Text accessibilityRole="alert" className="font-semibold">
            {t('account.privacy.deleteMealsError')}
          </Text>
        ) : null}
      </View>

      <View className="rounded-lg bg-surface px-lg">
        <ToggleRow
          testID="toggle-analytics"
          label={t('account.privacy.analytics')}
          detail={t('account.privacy.analyticsBody')}
          value={analyticsOn}
          disabled={analyticsSaving}
          onChange={setAnalytics}
        />
      </View>
      {analyticsFailed ? (
        <Text accessibilityRole="alert" className="font-semibold">
          {t('account.privacy.saveError')}
        </Text>
      ) : null}

      <View className="overflow-hidden rounded-lg bg-surface">
        <LinkRow testID="link-terms" icon="document-text-outline" label={t('account.privacy.terms')} url={TERMS_URL} />
        <LinkRow
          testID="link-privacy"
          icon="shield-checkmark-outline"
          label={t('account.privacy.policy')}
          url={PRIVACY_URL}
        />
      </View>
    </Screen>
  );
}
