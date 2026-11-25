import { Camera } from 'expo-camera';
import { router } from 'expo-router';
import { useCallback } from 'react';

import { isLimitReachedToday, useMealFlowStore } from '@/stores/mealFlow';

/**
 * "Registrar refeição" on Home: daily limit already hit today → 11; camera permission granted → 4;
 * otherwise → 9. The app only knows the limit was hit from a previous 429 (the API has no usage endpoint).
 */
export function useStartMealLog() {
  const limitReachedOn = useMealFlowStore((state) => state.limitReachedOn);
  const limitReached = isLimitReachedToday(limitReachedOn);

  const start = useCallback(async () => {
    useMealFlowStore.getState().reset();
    if (limitReached) {
      router.push('/meal/daily-limit');
      return;
    }
    const permission = await Camera.getCameraPermissionsAsync().catch(() => null);
    router.push(permission?.granted ? '/meal/camera' : '/meal/camera-permission');
  }, [limitReached]);

  return { start, limitReached };
}
