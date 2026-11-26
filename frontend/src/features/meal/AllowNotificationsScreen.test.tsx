import { fireEvent, screen } from '@testing-library/react-native';
import * as Notifications from 'expo-notifications';
import { router } from 'expo-router';

import { api } from '@/api/endpoints';
import { registerPushToken } from '@/features/notifications/pushToken';
import { makePet } from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';

import AllowNotificationsScreen from './AllowNotificationsScreen';

jest.mock('@/api/endpoints', () => ({ api: { getPet: jest.fn() } }));
jest.mock('expo-notifications', () => ({
  requestPermissionsAsync: jest.fn(),
  getPermissionsAsync: jest.fn(),
}));
jest.mock('@/features/notifications/pushToken', () => ({ registerPushToken: jest.fn(async () => true) }));

describe('<AllowNotificationsScreen /> (31)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getPet as jest.Mock).mockResolvedValue(makePet());
  });

  it('registers the push token after the user allows notifications', async () => {
    (Notifications.requestPermissionsAsync as jest.Mock).mockResolvedValue({ granted: true });
    await renderWithProviders(<AllowNotificationsScreen />);
    await fireEvent.press(screen.getByRole('button', { name: 'Permitir notificações' }));
    await screen.findByRole('button', { name: 'Permitir notificações' });
    expect(registerPushToken).toHaveBeenCalledTimes(1);
    expect(router.replace).toHaveBeenCalledWith('/(tabs)/home');
  });

  it('does not register a token when the system denies', async () => {
    (Notifications.requestPermissionsAsync as jest.Mock).mockResolvedValue({ granted: false });
    await renderWithProviders(<AllowNotificationsScreen />);
    await fireEvent.press(screen.getByRole('button', { name: 'Permitir notificações' }));
    await screen.findByRole('button', { name: 'Permitir notificações' });
    expect(registerPushToken).not.toHaveBeenCalled();
    expect(router.replace).toHaveBeenCalledWith('/(tabs)/home');
  });

  it('"Agora não" registers nothing and goes home', async () => {
    await renderWithProviders(<AllowNotificationsScreen />);
    await fireEvent.press(screen.getByRole('button', { name: 'Agora não' }));
    await screen.findByRole('button', { name: 'Agora não' });
    expect(registerPushToken).not.toHaveBeenCalled();
  });
});
