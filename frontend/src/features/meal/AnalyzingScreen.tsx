import { onlineManager, useQueryClient } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, ActivityIndicator, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { ApiError, NETWORK_ERROR } from '@/api/client';
import { api } from '@/api/endpoints';
import { queryKeys } from '@/api/queries';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useMealFlowStore } from '@/stores/mealFlow';
import { colors } from '@/theme/tokens';

import { classifyAnalysisFailure } from './analysisOutcome';
import { discardPhoto } from './photo';

const SLOW_MS = 10_000;

/** Screen 5: uploads the resized photo, announces progress, Cancel returns to Camera. */
export default function AnalyzingScreen() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const photoUri = useMealFlowStore((state) => state.photoUri);
  const setPhoto = useMealFlowStore((state) => state.setPhoto);
  const setResult = useMealFlowStore((state) => state.setResult);
  const markLimitReached = useMealFlowStore((state) => state.markLimitReached);
  const [slow, setSlow] = useState(false);
  const controller = useRef<AbortController | null>(null);

  const started = useRef(false);

  useEffect(() => {
    if (!photoUri) {
      // Opened without a photo (e.g. restored route): go back to the camera.
      if (!started.current) router.replace('/meal/camera');
      return;
    }
    started.current = true;
    const abort = new AbortController();
    controller.current = abort;
    AccessibilityInfo.announceForAccessibility(t('meal.analyzing.announce'));
    const slowTimer = setTimeout(() => {
      setSlow(true);
      AccessibilityInfo.announceForAccessibility(t('meal.analyzing.announceSlow'));
    }, SLOW_MS);

    // The photo file is kept (in memory reference only) while it waits for the connection.
    let keepPhoto = false;
    const holdForOffline = () => {
      keepPhoto = true;
      useMealFlowStore.getState().setPendingPhoto(photoUri);
      router.replace({ pathname: '/meal/error', params: { reason: 'offline' } });
    };

    const upload = onlineManager.isOnline()
      ? api.createMeal(photoUri, abort.signal)
      : Promise.reject(new ApiError(0, NETWORK_ERROR, ''));
    upload

      .then((created) => {
        setResult(created);
        queryClient.setQueryData(queryKeys.pet, created.pet);
        void queryClient.invalidateQueries({ queryKey: ['meals'] });
        router.replace('/meal/result');
      })
      .catch((error: unknown) => {
        const failure = classifyAnalysisFailure(error);
        switch (failure.kind) {
          case 'cancelled':
            return;
          case 'dailyLimit':
            markLimitReached();
            router.replace('/meal/daily-limit');
            return;
          case 'consentRequired':
            router.replace('/(onboarding)/age-terms');
            return;
          case 'error':
            if (failure.reason === 'offline') holdForOffline();
            else router.replace({ pathname: '/meal/error', params: { reason: failure.reason } });
        }
      })
      .finally(() => {
        clearTimeout(slowTimer);
        // The photo is never kept: drop the temporary file whatever the outcome (except while offline).
        if (!keepPhoto) discardPhoto(photoUri);
        setPhoto(null);
      });

    return () => {
      clearTimeout(slowTimer);
      abort.abort();
    };
    // Run once per photo.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [photoUri]);

  const cancel = () => {
    controller.current?.abort();
    router.replace('/meal/camera');
  };

  return (
    <Screen
      footer={<Button action="secondary" label={t('common.cancel')} onPress={cancel} />}
    >
      <View
        className="flex-1 items-center justify-center gap-lg"
        accessible
        accessibilityLiveRegion="polite"
        accessibilityState={{ busy: true }}
      >
        <ActivityIndicator size="large" color={colors.primary} />
        <Text variant="title" className="text-center">
          {t('meal.analyzing.title')}
        </Text>
        {slow ? (
          <Text variant="secondary" className="text-center">
            {t('meal.analyzing.slow')}
          </Text>
        ) : null}
      </View>
    </Screen>
  );
}
