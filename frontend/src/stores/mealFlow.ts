import { create } from 'zustand';

import type { MealCreated } from '@/api/types';
import { localDayKey } from '@/utils/date';

/**
 * In-memory UI state for the "log a meal" flow (flow 2). Nothing here is persisted:
 * the photo URI points to a temporary file that is deleted after the upload.
 */
interface MealFlowState {
  photoUri: string | null;
  /**
   * Photo waiting for the connection to come back (screen 10, offline). Memory only: if the app is killed
   * the pending photo is lost by design. The photo itself is never copied anywhere else.
   */
  pendingPhotoUri: string | null;
  setPendingPhoto: (uri: string | null) => void;
  result: MealCreated | null;
  /** Local day (YYYY-MM-DD) on which the API answered DAILY_LIMIT_REACHED. */
  limitReachedOn: string | null;
  setPhoto: (uri: string | null) => void;
  setResult: (result: MealCreated | null) => void;
  markLimitReached: (now?: Date) => void;
  reset: () => void;
}

export const useMealFlowStore = create<MealFlowState>((set) => ({
  photoUri: null,
  pendingPhotoUri: null,
  setPendingPhoto: (pendingPhotoUri) => set({ pendingPhotoUri }),
  result: null,
  limitReachedOn: null,
  setPhoto: (photoUri) => set({ photoUri }),
  setResult: (result) => set({ result }),
  markLimitReached: (now = new Date()) => set({ limitReachedOn: localDayKey(now) }),
  reset: () => set({ photoUri: null, pendingPhotoUri: null, result: null }),
}));

/** True when the daily limit was hit earlier today (resets at local midnight). */
export function isLimitReachedToday(limitReachedOn: string | null, now = new Date()): boolean {
  return limitReachedOn !== null && limitReachedOn === localDayKey(now);
}
