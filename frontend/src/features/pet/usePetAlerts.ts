import { router } from 'expo-router';
import { useEffect } from 'react';

import type { Pet } from '@/api/types';
import { usePetAlertStore } from '@/stores/petAlerts';

/**
 * Flow 6: when Home opens, show 12 (mood `fainted`) or 28 (event `life_lost`).
 * Both come from the API; fainted wins when both apply (0 lives).
 */
export function usePetAlerts(pet: Pet | undefined): void {
  const lifeLostPending = usePetAlertStore((state) => state.lifeLostPending);
  const faintedShown = usePetAlertStore((state) => state.faintedShown);
  const mood = pet?.mood;
  const named = pet != null && pet.name !== null;

  useEffect(() => {
    if (!mood || !named) return;
    const store = usePetAlertStore.getState();
    if (mood === 'fainted') {
      store.clearLifeLost();
      if (!faintedShown) {
        store.setFaintedShown(true);
        router.push('/pet/fainted');
      }
      return;
    }
    if (faintedShown) store.setFaintedShown(false);
    if (lifeLostPending) {
      store.clearLifeLost();
      router.push('/pet/life-lost');
    }
  }, [mood, named, lifeLostPending, faintedShown]);
}
