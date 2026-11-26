import * as SecureStore from 'expo-secure-store';

import type { TokenPair } from './types';

const ACCESS_KEY = 'papeto.access_token';
const REFRESH_KEY = 'papeto.refresh_token';

/** Tokens live only in expo-secure-store. Never log them. */
export const tokenStorage = {
  async get(): Promise<TokenPair | null> {
    const [access, refresh] = await Promise.all([
      SecureStore.getItemAsync(ACCESS_KEY),
      SecureStore.getItemAsync(REFRESH_KEY),
    ]);
    if (!access || !refresh) return null;
    return { access_token: access, refresh_token: refresh };
  },
  async set(tokens: TokenPair): Promise<void> {
    await Promise.all([
      SecureStore.setItemAsync(ACCESS_KEY, tokens.access_token),
      SecureStore.setItemAsync(REFRESH_KEY, tokens.refresh_token),
    ]);
  },
  async clear(): Promise<void> {
    await Promise.all([
      SecureStore.deleteItemAsync(ACCESS_KEY),
      SecureStore.deleteItemAsync(REFRESH_KEY),
    ]);
  },
};
