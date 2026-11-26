import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useRef } from 'react';
import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Icon, type IconName } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { useOnline } from '@/hooks/useOnline';
import { useMealFlowStore } from '@/stores/mealFlow';
import { colors } from '@/theme/tokens';

import { ANALYSIS_ERROR_REASONS, type AnalysisErrorReason } from './analysisOutcome';
import { discardPhoto } from './photo';
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
  const pending = useMealFlowStore((state) => state.pendingPhotoUri);
  const online = useOnline();
  const wasOnline = useRef(online);

  /** Sends the photo that waited in memory (offline queue). */
  const sendPending = () => {
    const store = useMealFlowStore.getState();
    if (!store.pendingPhotoUri) return;
    store.setPhoto(store.pendingPhotoUri);
    store.setPendingPhoto(null);
    router.replace('/meal/analyzing');
  };

  /** Leaving this screen any other way drops the queued photo (it is never kept). */
  const dropPending = () => {
    const store = useMealFlowStore.getState();
    discardPhoto(store.pendingPhotoUri);
    store.setPendingPhoto(null);
  };

  // Only a real offline -> online change triggers the retry, so a server outage cannot loop.
  useEffect(() => {
    if (online && !wasOnline.current && pending) sendPending();
    wasOnline.current = online;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [online]);

  const waiting = pending !== null && reason === 'offline';

  return (
    <Screen
      footer={
        <>
          {waiting ? (
            <Button
              testID="error-send-pending"
              label={t('meal.error.sendPending')}
              disabled={!online}
              onPress={sendPending}
            />
          ) : null}
          <Button
            testID="error-retry"
            action={waiting ? 'secondary' : 'primary'}
            label={t('meal.error.retry')}
            onPress={() => {
              dropPending();
              router.replace('/meal/camera');
            }}
          />
          <Button
            testID="error-manual"
            action="secondary"
            label={t('meal.error.manual')}
            onPress={() => {
              dropPending();
              router.replace('/meal/manual');
            }}
          />
          <Button
            action="secondary"
            label={t('meal.error.gallery')}
            loading={preparing}
            onPress={() => {
              dropPending();
              void fromGallery();
            }}
          />
          <Button
            action="ghost"
            label={t('common.back')}
            onPress={() => {
              dropPending();
              router.replace('/(tabs)/home');
            }}
          />
        </>
      }
    >
      <Icon name={icons[reason]} size={56} color={colors.primary} />
      <Text variant="title">{t('meal.error.title')}</Text>
      <Text testID="error-reason" accessibilityRole="alert">
        {t(`meal.error.${reason}`)}
      </Text>
      {waiting ? (
        <View testID="offline-queue" accessible className="gap-xs rounded-lg bg-surface p-lg">
          <Text className="font-heading">{t('meal.error.queueTitle')}</Text>
          <Text variant="secondary">{t('meal.error.queueBody')}</Text>
        </View>
      ) : null}
      <Text variant="secondary">{t('meal.error.notCounted')}</Text>
    </Screen>
  );
}
