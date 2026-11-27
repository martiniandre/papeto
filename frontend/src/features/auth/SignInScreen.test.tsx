import { fireEvent, screen, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';

import { ApiError } from '@/api/client';
import { api } from '@/api/endpoints';
import { renderWithProviders } from '@/test/render';

import SignInScreen from './SignInScreen';
import { GoogleSignInError, useGoogleSignIn } from './useGoogleSignIn';

jest.mock('@/api/endpoints', () => ({
  api: { googleSignIn: jest.fn(), getMe: jest.fn(), getPet: jest.fn() },
}));
jest.mock('./useGoogleSignIn', () => ({
  ...jest.requireActual('./useGoogleSignIn'),
  useGoogleSignIn: jest.fn(),
}));

const tokens = { access_token: 'a', refresh_token: 'r', token_type: 'bearer', expires_in: 900 };
const consents = ['terms_privacy', 'meal_data'].map((type) => ({
  type,
  version: '1.0',
  accepted: true,
  recorded_at: '2026-11-26T10:00:00Z',
}));
const signIn = jest.fn();
const googleButton = () => screen.getByRole('button', { name: 'Entrar com Google' });

async function pressGoogle() {
  await renderWithProviders(<SignInScreen />);
  await fireEvent.press(googleButton());
}

describe('<SignInScreen /> (screen 1) with Google', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    signIn.mockResolvedValue('google-id-token');
    (useGoogleSignIn as jest.Mock).mockReturnValue({ available: true, signIn });
  });

  it('has a labelled Google button, no Apple button, and e-mail', async () => {
    await renderWithProviders(<SignInScreen />);
    expect(googleButton()).toBeEnabled();
    expect(screen.queryByText(/Apple/)).toBeNull();
    expect(screen.getByRole('button', { name: 'Entrar com e-mail' })).toBeEnabled();
  });

  it('shows progress and disables the other buttons while signing in', async () => {
    (api.googleSignIn as jest.Mock).mockReturnValue(new Promise(() => undefined));
    await pressGoogle();
    await waitFor(() => expect(screen.getByText('Entrando com o Google…')).toBeOnTheScreen());
    expect(googleButton()).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Entrar com e-mail' })).toBeDisabled();
  });

  it('sends the id token with the device timezone and stores the tokens', async () => {
    (api.googleSignIn as jest.Mock).mockResolvedValue({ ...tokens, is_new_user: true });
    await pressGoogle();
    await waitFor(() => expect(router.replace).toHaveBeenCalled());
    expect(api.googleSignIn).toHaveBeenCalledWith({
      id_token: 'google-id-token',
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    });
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const store = (require('expo-secure-store') as { __store: Map<string, string> }).__store;
    expect(store.get('papeto.access_token')).toBe('a');
  });

  it('routes a new user to Age and terms', async () => {
    (api.googleSignIn as jest.Mock).mockResolvedValue({ ...tokens, is_new_user: true });
    await pressGoogle();
    await waitFor(() => expect(router.replace).toHaveBeenCalledWith('/(onboarding)/age-terms'));
    expect(api.getMe).not.toHaveBeenCalled();
  });

  it('routes an existing, unconfirmed adult to Age and terms without asking for the pet', async () => {
    (api.googleSignIn as jest.Mock).mockResolvedValue({ ...tokens, is_new_user: false });
    (api.getMe as jest.Mock).mockResolvedValue({ adult_confirmed: false, consents });
    await pressGoogle();
    await waitFor(() => expect(router.replace).toHaveBeenCalledWith('/(onboarding)/age-terms'));
    expect(api.getPet).not.toHaveBeenCalled();
  });

  it('routes an existing account with an unnamed pet to Name your pet', async () => {
    (api.googleSignIn as jest.Mock).mockResolvedValue({ ...tokens, is_new_user: false });
    (api.getMe as jest.Mock).mockResolvedValue({ adult_confirmed: true, consents });
    (api.getPet as jest.Mock).mockResolvedValue({ name: null });
    await pressGoogle();
    await waitFor(() => expect(router.replace).toHaveBeenCalledWith('/(onboarding)/name-pet'));
  });

  it('routes a complete existing account to Home', async () => {
    (api.googleSignIn as jest.Mock).mockResolvedValue({ ...tokens, is_new_user: false });
    (api.getMe as jest.Mock).mockResolvedValue({ adult_confirmed: true, consents });
    (api.getPet as jest.Mock).mockResolvedValue({ name: 'Bolinha' });
    await pressGoogle();
    await waitFor(() => expect(router.replace).toHaveBeenCalledWith('/(tabs)/home'));
  });

  it.each([
    ['GOOGLE_TOKEN_INVALID', 401, /confirmar sua conta Google/],
    ['GOOGLE_EMAIL_NOT_VERIFIED', 401, /e-mail desta conta Google não foi verificado/],
    ['AUTH_PROVIDER_UNAVAILABLE', 503, /login com Google está fora do ar/],
  ])('shows its own message for %s and re-enables the button', async (code, status, text) => {
    (api.googleSignIn as jest.Mock).mockRejectedValue(new ApiError(status, code, ''));
    await pressGoogle();
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(text));
    expect(googleButton()).toBeEnabled();
    expect(router.replace).not.toHaveBeenCalled();
  });

  it('stays silent when the user cancels the Google picker', async () => {
    signIn.mockRejectedValue(new GoogleSignInError('cancelled'));
    await pressGoogle();
    await waitFor(() => expect(googleButton()).toBeEnabled());
    expect(screen.queryByRole('alert')).toBeNull();
    expect(api.googleSignIn).not.toHaveBeenCalled();
  });

  it('shows a generic message when Google fails', async () => {
    signIn.mockRejectedValue(new GoogleSignInError('failed'));
    await pressGoogle();
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/Não deu para entrar com o Google/),
    );
  });

  it('shows "não disponível nesta versão" when the native module is missing (Expo Go)', async () => {
    (useGoogleSignIn as jest.Mock).mockReturnValue({ available: false, signIn });
    await pressGoogle();
    expect(screen.getByRole('alert')).toHaveTextContent(/não está disponível nesta versão/);
    expect(signIn).not.toHaveBeenCalled();
  });
});
