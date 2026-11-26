import * as Notifications from 'expo-notifications';
import * as SecureStore from 'expo-secure-store';

import { registerPushToken } from '@/features/notifications/pushToken';

const SNOOZE_KEY = 'papeto.notifications_snoozed_at';
export const SNOOZE_DAYS = 7;
const DAY_MS = 24 * 60 * 60 * 1000;

/**
 * Screen 31 shows after the first meal only. "First meal" is read as: the system permission was
 * never asked and the user did not tap "Agora não" in the last 7 days.
 */
export async function shouldAskForNotifications(now = Date.now()): Promise<boolean> {
  try {
    const { status } = await Notifications.getPermissionsAsync();
    if (status !== 'undetermined') return false;
    const snoozedAt = Number((await SecureStore.getItemAsync(SNOOZE_KEY)) ?? 0);
    return !snoozedAt || now - snoozedAt >= SNOOZE_DAYS * DAY_MS;
  } catch {
    return false;
  }
}

export async function snoozeNotificationsPrompt(now = Date.now()): Promise<void> {
  await SecureStore.setItemAsync(SNOOZE_KEY, String(now));
}

/** Asks the OS; when allowed, registers the Expo push token with POST /push-tokens (failure is silent). */
export async function requestNotifications(): Promise<boolean> {
  const { granted } = await Notifications.requestPermissionsAsync();
  if (granted) await registerPushToken();
  return granted;
}
