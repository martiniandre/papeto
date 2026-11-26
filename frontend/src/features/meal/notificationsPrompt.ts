import * as Notifications from 'expo-notifications';
import * as SecureStore from 'expo-secure-store';

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

/** Asks the OS. Registering the Expo push token needs an API endpoint not in docs/api.md yet. */
export async function requestNotifications(): Promise<boolean> {
  const { granted } = await Notifications.requestPermissionsAsync();
  return granted;
}
