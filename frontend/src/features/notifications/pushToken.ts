import Constants from 'expo-constants';
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

import { api } from '@/api/endpoints';

function easProjectId(): string | undefined {
  const extra = Constants.expoConfig?.extra as { eas?: { projectId?: string } } | undefined;
  return extra?.eas?.projectId ?? Constants.easConfig?.projectId;
}

/**
 * Reads the Expo push token and registers it with POST /push-tokens. Call it only after the user allowed
 * notifications. Returns false when there is no token (simulator, no project id) or the API refused;
 * a failure here never blocks the user, and the token is never logged.
 */
export async function registerPushToken(): Promise<boolean> {
  try {
    const { data } = await Notifications.getExpoPushTokenAsync({ projectId: easProjectId() });
    await api.registerPushToken({ token: data, platform: Platform.OS === 'ios' ? 'ios' : 'android' });
    return true;
  } catch {
    return false;
  }
}
