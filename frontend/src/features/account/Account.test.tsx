import { act, fireEvent, screen, waitFor } from '@testing-library/react-native';
import * as Notifications from 'expo-notifications';
import { router } from 'expo-router';
import { Linking, Share } from 'react-native';

import { ApiError } from '@/api/client';
import { api } from '@/api/endpoints';
import type { Me } from '@/api/types';
import ProfileScreen from '@/features/profile/ProfileScreen';
import { useSessionStore } from '@/stores/session';
import { makePet } from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';

import AccountDeletedScreen from './AccountDeletedScreen';
import DeleteAccountScreen from './DeleteAccountScreen';
import ExportDataScreen from './ExportDataScreen';
import NotificationsSettingsScreen from './NotificationsSettingsScreen';

jest.mock('@/api/endpoints', () => ({
  api: { getMe: jest.fn(), updateMe: jest.fn(), getPet: jest.fn(), deleteAccount: jest.fn(), exportData: jest.fn() },
}));
jest.mock('expo-notifications', () => ({ getPermissionsAsync: jest.fn() }));
jest.setTimeout(30000);

const me = (overrides: Partial<Me> = {}): Me => ({
  id: 'u1',
  email: 'ana@example.com',
  name: 'Ana',
  timezone: 'America/Sao_Paulo',
  plan: 'free',
  analytics_opt_out: false,
  adult_confirmed: true,
  notifications: {
    meal_reminder: true,
    sleepy_notice: true,
    weekly_summary: false,
    quiet_hours_start: '22:00',
    quiet_hours_end: '08:00',
  },
  consents: [],
  deletion_scheduled_for: null,
  ...overrides,
});

describe('profile flow (screens 8, 27, 36, 35, 41)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getMe as jest.Mock).mockResolvedValue(me());
    (api.getPet as jest.Mock).mockResolvedValue(makePet());
    (Notifications.getPermissionsAsync as jest.Mock).mockResolvedValue({ status: 'granted' });
  });

  describe('<ProfileScreen /> (8)', () => {
    it('shows loading, then profile data with labelled rows', async () => {
      (api.getMe as jest.Mock).mockReturnValue(new Promise(() => undefined));
      const { unmount } = await renderWithProviders(<ProfileScreen />);
      expect(screen.getByLabelText('Carregando')).toBeOnTheScreen();
      unmount();
    });

    it('renders name, email, timezone and every entry point', async () => {
      await renderWithProviders(<ProfileScreen />);
      expect(await screen.findByText('Ana')).toBeOnTheScreen();
      expect(screen.getByText('ana@example.com')).toBeOnTheScreen();
      expect(screen.getByLabelText('Fuso horário, Sao Paulo')).toBeOnTheScreen();
      expect(screen.getByRole('button', { name: 'Avisos do pet, Ligados' })).toBeOnTheScreen();
      expect(screen.getByRole('button', { name: 'Pausar o pet, Premium' })).toBeOnTheScreen();
      expect(screen.getByRole('button', { name: 'Exportar meus dados' })).toBeOnTheScreen();
      expect(screen.getByRole('button', { name: 'Privacidade' })).toBeOnTheScreen();
      expect(screen.getByRole('button', { name: 'Apoio' })).toBeOnTheScreen();
      expect(screen.getByRole('button', { name: 'Sair' })).toBeOnTheScreen();
      expect(screen.getByRole('button', { name: 'Excluir conta' })).toBeOnTheScreen();
    });

    it('navigates to notifications, export, delete account and Premium', async () => {
      await renderWithProviders(<ProfileScreen />);
      await fireEvent.press(await screen.findByTestId('row-notifications'));
      expect(router.push).toHaveBeenLastCalledWith('/account/notifications');
      await fireEvent.press(screen.getByTestId('row-export'));
      expect(router.push).toHaveBeenLastCalledWith('/account/export');
      await fireEvent.press(screen.getByTestId('delete-account-link'));
      expect(router.push).toHaveBeenLastCalledWith('/account/delete');
      await fireEvent.press(screen.getByTestId('row-privacy'));
      expect(router.push).toHaveBeenLastCalledWith('/account/privacy');
      await fireEvent.press(screen.getByTestId('row-support'));
      expect(router.push).toHaveBeenLastCalledWith('/account/support');
      await fireEvent.press(screen.getByTestId('row-pause'));
      expect(router.push).toHaveBeenLastCalledWith('/premium');
    });

    it('shows the error state with retry', async () => {
      (api.getMe as jest.Mock).mockRejectedValue(new ApiError(500, 'UNKNOWN_ERROR', ''));
      await renderWithProviders(<ProfileScreen />);
      expect(await screen.findByRole('button', { name: 'Tentar de novo' })).toBeOnTheScreen();
    });
  });

  describe('<NotificationsSettingsScreen /> (27)', () => {
    it('exposes toggles as switches with their state and saves a change with PATCH /me', async () => {
      (api.updateMe as jest.Mock).mockResolvedValue(
        me({
          notifications: {
            meal_reminder: true,
            sleepy_notice: true,
            weekly_summary: true,
            quiet_hours_start: '22:00',
            quiet_hours_end: '08:00',
          },
        }),
      );
      await renderWithProviders(<NotificationsSettingsScreen />);
      const weekly = await screen.findByRole('switch', { name: 'Resumo semanal' });
      expect(weekly).not.toBeChecked();
      await fireEvent.press(weekly);
      expect(api.updateMe).toHaveBeenCalledWith({ notifications: { weekly_summary: true } });
      await waitFor(() => expect(screen.getByRole('switch', { name: 'Resumo semanal' })).toBeChecked());
      expect(screen.getByRole('switch', { name: 'Lembrete de refeição' })).toBeChecked();
      expect(screen.getByRole('switch', { name: 'Não incomodar, 22:00 às 08:00' })).toBeOnTheScreen();
      expect(screen.queryByTestId('notifications-denied')).toBeNull();
    });

    it('turns quiet hours off by sending equal start and end', async () => {
      (api.updateMe as jest.Mock).mockResolvedValue(me());
      await renderWithProviders(<NotificationsSettingsScreen />);
      await fireEvent.press(await screen.findByRole('switch', { name: 'Não incomodar, 22:00 às 08:00' }));
      expect(api.updateMe).toHaveBeenCalledWith({
        notifications: { quiet_hours_start: '00:00', quiet_hours_end: '00:00' },
      });
    });

    it('shows a message when saving fails', async () => {
      (api.updateMe as jest.Mock).mockRejectedValue(new ApiError(500, 'UNKNOWN_ERROR', ''));
      await renderWithProviders(<NotificationsSettingsScreen />);
      await fireEvent.press(await screen.findByRole('switch', { name: 'Resumo semanal' }));
      expect(await screen.findByText('Não deu para salvar a mudança. Tente de novo.')).toBeOnTheScreen();
    });

    it('shows the error state with retry when preferences cannot load', async () => {
      (api.getMe as jest.Mock).mockRejectedValue(new ApiError(500, 'UNKNOWN_ERROR', ''));
      await renderWithProviders(<NotificationsSettingsScreen />);
      expect(await screen.findByRole('button', { name: 'Tentar de novo' })).toBeOnTheScreen();
    });

    it('links to the system Settings when notifications are denied', async () => {
      (Notifications.getPermissionsAsync as jest.Mock).mockResolvedValue({ status: 'denied' });
      const openSettings = jest.spyOn(Linking, 'openSettings').mockResolvedValue(undefined);
      await renderWithProviders(<NotificationsSettingsScreen />);
      expect(await screen.findByTestId('notifications-denied')).toBeOnTheScreen();
      await fireEvent.press(screen.getByRole('button', { name: 'Abrir Ajustes' }));
      expect(openSettings).toHaveBeenCalled();
    });

    it('has a labelled back button', async () => {
      await renderWithProviders(<NotificationsSettingsScreen />);
      await fireEvent.press(await screen.findByRole('button', { name: 'Voltar' }));
      expect(router.back).toHaveBeenCalled();
    });
  });

  describe('<ExportDataScreen /> (36)', () => {
    it('is free, lists the content and shares the JSON', async () => {
      (api.exportData as jest.Mock).mockResolvedValue({ user: { id: 'u1' } });
      const share = jest.spyOn(Share, 'share').mockResolvedValue({ action: 'sharedAction', activityType: undefined });
      await renderWithProviders(<ExportDataScreen />);
      expect(screen.getByText('Exportar é sempre grátis.')).toBeOnTheScreen();
      expect(screen.getByText('Conta e consentimentos')).toBeOnTheScreen();
      await fireEvent.press(screen.getByRole('button', { name: 'Exportar arquivo (JSON)' }));
      expect(await screen.findByTestId('export-ready')).toBeOnTheScreen();
      expect(api.exportData).toHaveBeenCalledTimes(1);
      expect(share).toHaveBeenCalledWith(expect.objectContaining({ message: expect.stringContaining('"u1"') }));
    });

    it('shows a failure message and lets the user try again', async () => {
      (api.exportData as jest.Mock).mockRejectedValue(new ApiError(500, 'UNKNOWN_ERROR', ''));
      await renderWithProviders(<ExportDataScreen />);
      await fireEvent.press(screen.getByRole('button', { name: 'Exportar arquivo (JSON)' }));
      expect(await screen.findByTestId('export-failed')).toBeOnTheScreen();
      expect(screen.getByRole('button', { name: 'Exportar arquivo (JSON)' })).toBeOnTheScreen();
    });

    it('shows the offline state with retry', async () => {
      (api.exportData as jest.Mock).mockRejectedValue(new ApiError(0, 'NETWORK_ERROR', ''));
      await renderWithProviders(<ExportDataScreen />);
      await fireEvent.press(screen.getByRole('button', { name: 'Exportar arquivo (JSON)' }));
      expect(await screen.findByRole('button', { name: 'Tentar de novo' })).toBeOnTheScreen();
    });
  });

  describe('<DeleteAccountScreen /> (35)', () => {
    it('keeps the button disabled until the confirmation is checked', async () => {
      (api.deleteAccount as jest.Mock).mockResolvedValue({ deletion_scheduled_for: '2026-12-31' });
      await renderWithProviders(<DeleteAccountScreen />);
      expect(screen.getByRole('button', { name: 'Excluir conta' })).toBeDisabled();
      expect(screen.getByText('Marque a confirmação acima para liberar')).toBeOnTheScreen();
      await fireEvent.press(screen.getByRole('button', { name: 'Excluir conta' }));
      expect(api.deleteAccount).not.toHaveBeenCalled();

      await fireEvent.press(
        screen.getByRole('checkbox', { name: 'Entendo que isso não pode ser desfeito depois de 30 dias' }),
      );
      expect(screen.getByRole('button', { name: 'Excluir conta' })).toBeEnabled();
      await fireEvent.press(screen.getByRole('button', { name: 'Excluir conta' }));
      await act(async () => {});
      expect(api.deleteAccount).toHaveBeenCalledTimes(1);
      expect(router.replace).toHaveBeenCalledWith('/(onboarding)/account-deleted');
    });

    it('shows a message and stays on the screen when deleting fails', async () => {
      (api.deleteAccount as jest.Mock).mockRejectedValue(new ApiError(500, 'UNKNOWN_ERROR', ''));
      await renderWithProviders(<DeleteAccountScreen />);
      await fireEvent.press(screen.getByRole('checkbox'));
      await fireEvent.press(screen.getByRole('button', { name: 'Excluir conta' }));
      expect(await screen.findByTestId('delete-account-failed')).toBeOnTheScreen();
      expect(router.replace).not.toHaveBeenCalled();
    });

    it('offers export first and "Manter minha conta"', async () => {
      await renderWithProviders(<DeleteAccountScreen />);
      await fireEvent.press(screen.getByRole('button', { name: 'Antes, exportar meus dados' }));
      expect(router.push).toHaveBeenCalledWith('/account/export');
      await fireEvent.press(screen.getByRole('button', { name: 'Manter minha conta' }));
      expect(router.back).toHaveBeenCalled();
    });
  });

  describe('<AccountDeletedScreen /> (41)', () => {
    it('ends the local session and goes back to sign in', async () => {
      useSessionStore.getState().setStatus('signedIn');
      await renderWithProviders(<AccountDeletedScreen />);
      expect(screen.getByText('Sua conta foi excluída')).toBeOnTheScreen();
      await act(async () => {});
      expect(useSessionStore.getState().status).toBe('signedOut');
      await fireEvent.press(screen.getByRole('button', { name: 'Voltar para a tela de entrada' }));
      expect(router.replace).toHaveBeenCalledWith('/(onboarding)/sign-in');
    });
  });
});
