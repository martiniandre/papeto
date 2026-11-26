import type { QueryClient } from '@tanstack/react-query';
import { create } from 'zustand';

import { api } from '@/api/endpoints';
import { queryKeys } from '@/api/queries';

/** The API has no restore endpoint, so the undo window is client-side (docs/api.md). */
export const UNDO_WINDOW_MS = 5000;

interface PendingDeleteState {
  /** Meal hidden from the lists while its undo window is open. */
  pendingId: string | null;
  /** True after the DELETE call failed (the meal is back in the list). */
  failed: boolean;
  setPending: (id: string | null) => void;
  setFailed: (failed: boolean) => void;
}

export const usePendingDeleteStore = create<PendingDeleteState>((set) => ({
  pendingId: null,
  failed: false,
  setPending: (pendingId) => set({ pendingId }),
  setFailed: (failed) => set({ failed }),
}));

let timer: ReturnType<typeof setTimeout> | null = null;
let current: { id: string; client: QueryClient } | null = null;

async function commit(id: string, client: QueryClient): Promise<void> {
  try {
    await api.deleteMeal(id);
    usePendingDeleteStore.getState().setPending(null);
    client.removeQueries({ queryKey: queryKeys.meal(id) });
  } catch {
    usePendingDeleteStore.setState({ pendingId: null, failed: true });
  }
  await client.invalidateQueries({ queryKey: queryKeys.mealsAll });
}

/** Sends the pending DELETE now (a new delete started, or the window ended). */
export function flushPendingDelete(): Promise<void> {
  if (!current) return Promise.resolve();
  if (timer) clearTimeout(timer);
  timer = null;
  const { id, client } = current;
  current = null;
  return commit(id, client);
}

/**
 * Hides the meal and calls DELETE only after 5 s without "Desfazer".
 * Points and lives never change (docs/domain/pet-rules.md), so the pet is not refetched.
 */
export function scheduleMealDelete(id: string, client: QueryClient): void {
  void flushPendingDelete();
  usePendingDeleteStore.setState({ pendingId: id, failed: false });
  current = { id, client };
  timer = setTimeout(() => void flushPendingDelete(), UNDO_WINDOW_MS);
}

export function undoMealDelete(): void {
  if (timer) clearTimeout(timer);
  timer = null;
  current = null;
  usePendingDeleteStore.getState().setPending(null);
}
