import type { QueryClient } from '@tanstack/react-query';

import { setUnauthorizedListener } from '@/api/client';
import { tokenStorage } from '@/api/tokenStorage';
import type { TokenPair } from '@/api/types';
import { useSessionStore } from '@/stores/session';

export async function restoreSession(): Promise<void> {
  const tokens = await tokenStorage.get().catch(() => null);
  useSessionStore.getState().setStatus(tokens ? 'signedIn' : 'signedOut');
}

export async function startSession(tokens: TokenPair): Promise<void> {
  await tokenStorage.set(tokens);
  useSessionStore.getState().setStatus('signedIn');
}

export async function endSession(queryClient: QueryClient): Promise<void> {
  await tokenStorage.clear();
  queryClient.clear();
  useSessionStore.getState().setStatus('signedOut');
}

/** Signs out locally when the API refuses the refresh token. */
export function listenForExpiredSession(queryClient: QueryClient): void {
  setUnauthorizedListener(() => {
    queryClient.clear();
    useSessionStore.getState().setStatus('signedOut');
  });
}
