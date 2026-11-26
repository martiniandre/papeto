import { fireEvent, screen } from '@testing-library/react-native';
import { router } from 'expo-router';
import { Linking } from 'react-native';

import { renderWithProviders } from '@/test/render';

import SupportScreen from './SupportScreen';

describe('<SupportScreen /> (Profile > Apoio)', () => {
  beforeEach(() => jest.clearAllMocks());

  it('says the app does not replace a doctor or nutritionist', async () => {
    await renderWithProviders(<SupportScreen />);
    expect(screen.getByTestId('support-notice')).toHaveTextContent(/não substitui médico ou nutricionista/);
  });

  it('links to CVV 188 by phone and to cvv.org.br', async () => {
    const open = jest.spyOn(Linking, 'openURL').mockResolvedValue();
    await renderWithProviders(<SupportScreen />);
    await fireEvent.press(screen.getByRole('button', { name: 'Ligar para o CVV, telefone 188' }));
    expect(open).toHaveBeenCalledWith('tel:188');
    await fireEvent.press(screen.getByRole('button', { name: 'Abrir o site do CVV, cvv.org.br' }));
    expect(open).toHaveBeenCalledWith('https://cvv.org.br');
  });

  it('has a labelled back button', async () => {
    await renderWithProviders(<SupportScreen />);
    await fireEvent.press(screen.getByRole('button', { name: 'Voltar' }));
    expect(router.back).toHaveBeenCalled();
  });
});
