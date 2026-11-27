import { fireEvent, screen, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';
import { Linking } from 'react-native';

import { ApiError } from '@/api/client';
import { api } from '@/api/endpoints';
import type { Me } from '@/api/types';
import { renderWithProviders } from '@/test/render';

import PrivacyScreen from './PrivacyScreen';
import { isConsentActive } from './usePrivacy';

jest.mock('@/api/endpoints', () => ({
  api: { getMe: jest.fn(), updateMe: jest.fn(), acceptConsent: jest.fn(), deleteAllMeals: jest.fn() },
}));
jest.setTimeout(30000);

const consent = (accepted: boolean, recorded_at: string) => ({
  type: 'meal_data' as const,
  version: '1.0',
  accepted,
  recorded_at,
});

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
  consents: [consent(true, '2026-01-01T10:00:00Z')],
  deletion_scheduled_for: null,
  ...overrides,
});

describe('isConsentActive', () => {
  it('uses the latest record of the type', () => {
    expect(isConsentActive({ consents: [] }, 'meal_data')).toBe(false);
    expect(
      isConsentActive(
        { consents: [consent(true, '2026-01-01T10:00:00Z'), consent(false, '2026-02-01T10:00:00Z')] },
        'meal_data',
      ),
    ).toBe(false);
  });
});

describe('<PrivacyScreen />', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getMe as jest.Mock).mockResolvedValue(me());
  });

  it('explains the effect before revoking, then sends accepted:false', async () => {
    (api.acceptConsent as jest.Mock).mockResolvedValue(undefined);
    await renderWithProviders(<PrivacyScreen />);
    expect(await screen.findByText('Autorização ativa')).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Revogar autorização' }));
    expect(screen.getByTestId('revoke-explain')).toHaveTextContent(/para de analisar fotos/);
    expect(api.acceptConsent).not.toHaveBeenCalled();

    (api.getMe as jest.Mock).mockResolvedValue(
      me({ consents: [consent(true, '2026-01-01T10:00:00Z'), consent(false, '2026-03-01T10:00:00Z')] }),
    );
    await fireEvent.press(screen.getByTestId('revoke-confirm'));
    await waitFor(() =>
      expect(api.acceptConsent).toHaveBeenCalledWith({ type: 'meal_data', version: '1.0', accepted: false }),
    );
    expect(await screen.findByText('Autorização revogada')).toBeOnTheScreen();
    expect(screen.getByTestId('revoked-note')).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Autorizar de novo' })).toBeOnTheScreen();
  });

  it('lets the user keep the consent', async () => {
    await renderWithProviders(<PrivacyScreen />);
    await fireEvent.press(await screen.findByRole('button', { name: 'Revogar autorização' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Manter autorização' }));
    expect(screen.queryByTestId('revoke-explain')).toBeNull();
    expect(api.acceptConsent).not.toHaveBeenCalled();
  });

  it('offers export and deletes meal records only after a confirmation', async () => {
    (api.deleteAllMeals as jest.Mock).mockResolvedValue(undefined);
    await renderWithProviders(<PrivacyScreen />);
    await fireEvent.press(await screen.findByTestId('privacy-export'));
    expect(router.push).toHaveBeenCalledWith('/account/export');

    await fireEvent.press(screen.getByRole('button', { name: 'Apagar meus registros de refeição' }));
    expect(api.deleteAllMeals).not.toHaveBeenCalled();
    await fireEvent.press(screen.getByTestId('delete-meals-confirm-button'));
    await waitFor(() => expect(api.deleteAllMeals).toHaveBeenCalledTimes(1));
    expect(await screen.findByTestId('meals-deleted-note')).toBeOnTheScreen();
  });

  it('shows a message when deleting the records fails', async () => {
    (api.deleteAllMeals as jest.Mock).mockRejectedValue(new ApiError(500, 'UNKNOWN_ERROR', ''));
    await renderWithProviders(<PrivacyScreen />);
    await fireEvent.press(await screen.findByTestId('delete-meals-start'));
    await fireEvent.press(screen.getByTestId('delete-meals-confirm-button'));
    expect(await screen.findByText('Não deu para apagar os registros. Tente de novo.')).toBeOnTheScreen();
  });

  it('turns analytics off with PATCH /me (opt-out)', async () => {
    (api.updateMe as jest.Mock).mockResolvedValue(me({ analytics_opt_out: true }));
    await renderWithProviders(<PrivacyScreen />);
    const toggle = await screen.findByRole('switch', {
      name: 'Estatísticas de uso, Dados anônimos para melhorar o app, sem nome e sem e-mail.',
    });
    expect(toggle).toBeChecked();
    await fireEvent.press(toggle);
    expect(api.updateMe).toHaveBeenCalledWith({ analytics_opt_out: true });
    await waitFor(() => expect(screen.getByTestId('toggle-analytics')).not.toBeChecked());
  });

  it('opens the Terms and the Privacy Policy from the configured URLs', async () => {
    const open = jest.spyOn(Linking, 'openURL').mockResolvedValue();
    await renderWithProviders(<PrivacyScreen />);
    await fireEvent.press(await screen.findByRole('link', { name: 'Termos de Uso' }));
    expect(open).toHaveBeenLastCalledWith(expect.stringMatching(/^https:\/\/.+termos/));
    await fireEvent.press(screen.getByRole('link', { name: 'Política de Privacidade' }));
    expect(open).toHaveBeenLastCalledWith(expect.stringMatching(/^https:\/\/.+privacidade/));
  });

  it('shows the error state with retry', async () => {
    (api.getMe as jest.Mock).mockRejectedValue(new ApiError(500, 'UNKNOWN_ERROR', ''));
    await renderWithProviders(<PrivacyScreen />);
    expect(await screen.findByRole('button', { name: 'Tentar de novo' })).toBeOnTheScreen();
  });

  it('has a labelled back button', async () => {
    await renderWithProviders(<PrivacyScreen />);
    await fireEvent.press(await screen.findByRole('button', { name: 'Voltar' }));
    expect(router.back).toHaveBeenCalled();
  });
});
