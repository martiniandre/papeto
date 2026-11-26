import * as Notifications from 'expo-notifications';

import { api } from '@/api/endpoints';

import { registerPushToken } from './pushToken';

jest.mock('@/api/endpoints', () => ({ api: { registerPushToken: jest.fn() } }));
jest.mock('expo-notifications', () => ({ getExpoPushTokenAsync: jest.fn() }));
jest.mock('expo-constants', () => ({
  __esModule: true,
  default: { expoConfig: { extra: { eas: { projectId: 'proj-1' } } } },
}));

describe('registerPushToken', () => {
  beforeEach(() => jest.clearAllMocks());

  it('sends the Expo token with the platform to POST /push-tokens', async () => {
    (Notifications.getExpoPushTokenAsync as jest.Mock).mockResolvedValue({ data: 'ExponentPushToken[abc]' });
    (api.registerPushToken as jest.Mock).mockResolvedValue({});
    await expect(registerPushToken()).resolves.toBe(true);
    expect(Notifications.getExpoPushTokenAsync).toHaveBeenCalledWith({ projectId: 'proj-1' });
    expect(api.registerPushToken).toHaveBeenCalledWith({
      token: 'ExponentPushToken[abc]',
      platform: expect.stringMatching(/^(ios|android)$/),
    });
  });

  it('returns false and does not throw when there is no token', async () => {
    (Notifications.getExpoPushTokenAsync as jest.Mock).mockRejectedValue(new Error('no device'));
    await expect(registerPushToken()).resolves.toBe(false);
    expect(api.registerPushToken).not.toHaveBeenCalled();
  });

  it('returns false when the API refuses the token', async () => {
    (Notifications.getExpoPushTokenAsync as jest.Mock).mockResolvedValue({ data: 'ExponentPushToken[abc]' });
    (api.registerPushToken as jest.Mock).mockRejectedValue(new Error('422'));
    await expect(registerPushToken()).resolves.toBe(false);
  });
});
