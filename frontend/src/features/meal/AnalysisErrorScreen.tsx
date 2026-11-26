import { router, useLocalSearchParams } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Icon, type IconName } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { colors } from '@/theme/tokens';

import { ANALYSIS_ERROR_REASONS, type AnalysisErrorReason } from './analysisOutcome';
import { useSubmitPhoto } from './useSubmitPhoto';

const icons: Record<AnalysisErrorReason, IconName> = {
  not_food: 'restaurant-outline',
  unreadable: 'contrast-outline',
  offline: 'cloud-offline-outline',
  ai_error: 'alert-circle-outline',
};

export function parseReason(value: unknown): AnalysisErrorReason {
  return ANALYSIS_ERROR_REASONS.includes(value as AnalysisErrorReason)
    ? (value as AnalysisErrorReason)
    : 'ai_error';
}

/** Screen 10: one text per failure; never counts toward the daily limit. */
export default function AnalysisErrorScreen() {
  const { t } = useTranslation();
  const params = useLocalSearchParams<{ reason?: string }>();
  const reason = parseReason(params.reason);
  const { fromGallery, preparing } = useSubmitPhoto();

  return (
    <Screen
      footer={
        <>
          <Button testID="error-retry" label={t('meal.error.retry')} onPress={() => router.replace('/meal/camera')} />
          <Button
            action="secondary"
            label={t('meal.error.gallery')}
            loading={preparing}
            onPress={() => void fromGallery()}
          />
          <Button action="ghost" label={t('common.back')} onPress={() => router.replace('/(tabs)/home')} />
        </>
      }
    >
      <Icon name={icons[reason]} size={56} color={colors.primary} />
      <Text variant="title">{t('meal.error.title')}</Text>
      <Text testID="error-reason" accessibilityRole="alert">
        {t(`meal.error.${reason}`)}
      </Text>
      <Text variant="secondary">{t('meal.error.notCounted')}</Text>
    </Screen>
  );
}
