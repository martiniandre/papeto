import { act, fireEvent, screen } from '@testing-library/react-native';
import { router, useLocalSearchParams } from 'expo-router';

import { ApiError } from '@/api/client';
import { api } from '@/api/endpoints';
import { renderWithProviders } from '@/test/render';

import ResetPasswordScreen from './ResetPasswordScreen';

jest.mock('@/api/endpoints', () => ({ api: { resetPassword: jest.fn() } }));
jest.setTimeout(30000);

describe('<ResetPasswordScreen />', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useLocalSearchParams as jest.Mock).mockReturnValue({ token: 'tok123' });
  });

  it('keeps the button disabled until a password is typed, then resets with the link token', async () => {
    (api.resetPassword as jest.Mock).mockResolvedValue(undefined);
    await renderWithProviders(<ResetPasswordScreen />);
    expect(screen.getByRole('button', { name: 'Salvar nova senha' })).toBeDisabled();
    await fireEvent.changeText(screen.getByLabelText('Nova senha'), 'senhaNova123');
    await fireEvent.press(screen.getByRole('button', { name: 'Salvar nova senha' }));
    await act(async () => {});
    expect(api.resetPassword).toHaveBeenCalledWith('tok123', 'senhaNova123');
    expect(await screen.findByText('Pronto! Entre com a sua nova senha.')).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Entrar' }));
    expect(router.replace).toHaveBeenCalledWith('/(onboarding)/email');
  });

  it('rejects a weak password without calling the API', async () => {
    await renderWithProviders(<ResetPasswordScreen />);
    await fireEvent.changeText(screen.getByLabelText('Nova senha'), 'abc');
    await fireEvent.press(screen.getByRole('button', { name: 'Salvar nova senha' }));
    await act(async () => {});
    expect(api.resetPassword).not.toHaveBeenCalled();
  });

  it('offers a new link when the token is rejected', async () => {
    (api.resetPassword as jest.Mock).mockRejectedValue(new ApiError(400, 'INVALID_RESET_TOKEN', ''));
    await renderWithProviders(<ResetPasswordScreen />);
    await fireEvent.changeText(screen.getByLabelText('Nova senha'), 'senhaNova123');
    await fireEvent.press(screen.getByRole('button', { name: 'Salvar nova senha' }));
    expect(await screen.findByTestId('reset-invalid')).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Pedir um novo link' }));
    expect(router.replace).toHaveBeenCalledWith('/(onboarding)/recover-password');
  });

  it('shows the invalid-link state when the link has no token', async () => {
    (useLocalSearchParams as jest.Mock).mockReturnValue({});
    await renderWithProviders(<ResetPasswordScreen />);
    expect(screen.getByTestId('reset-invalid')).toBeOnTheScreen();
  });
});
