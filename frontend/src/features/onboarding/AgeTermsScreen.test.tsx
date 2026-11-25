import { fireEvent, screen, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';

import { api } from '@/api/endpoints';
import { renderWithProviders } from '@/test/render';

import AgeTermsScreen from './AgeTermsScreen';

jest.mock('@/api/endpoints', () => ({ api: { acceptConsent: jest.fn(async () => undefined) } }));

describe('<AgeTermsScreen /> (screen 2)', () => {
  beforeEach(() => jest.clearAllMocks());

  const continueButton = () => screen.getByTestId('terms-continue');

  it('enables Continue only when both consents are checked', async () => {
    await renderWithProviders(<AgeTermsScreen />);
    expect(continueButton()).toBeDisabled();

    await fireEvent.press(screen.getByTestId('consent-terms'));
    expect(screen.getByTestId('consent-terms')).toBeChecked();
    expect(continueButton()).toBeDisabled();

    await fireEvent.press(screen.getByTestId('consent-meal-data'));
    expect(screen.getByTestId('consent-meal-data')).toBeChecked();
    expect(continueButton()).toBeEnabled();
  });

  it('exposes both consents as labelled checkboxes', async () => {
    await renderWithProviders(<AgeTermsScreen />);
    expect(screen.getAllByRole('checkbox')).toHaveLength(2);
    expect(
      screen.getByRole('checkbox', { name: /Termos de Uso e a Política de Privacidade/ }),
    ).toBeOnTheScreen();
    expect(screen.getByRole('checkbox', { name: /analisar as fotos/ })).toBeOnTheScreen();
  });

  it('records the two consents separately, then goes to Name your pet', async () => {
    await renderWithProviders(<AgeTermsScreen />);
    await fireEvent.press(screen.getByTestId('consent-terms'));
    await fireEvent.press(screen.getByTestId('consent-meal-data'));
    await fireEvent.press(continueButton());

    await waitFor(() => expect(router.replace).toHaveBeenCalledWith('/(onboarding)/name-pet'));
    expect(api.acceptConsent).toHaveBeenCalledWith({ type: 'terms_privacy', version: '1.0', accepted: true });
    expect(api.acceptConsent).toHaveBeenCalledWith({ type: 'meal_data', version: '1.0', accepted: true });
  });
});
