import { fireEvent, screen, waitFor } from '@testing-library/react-native';

import { renderWithProviders } from '@/test/render';

import CreateAccountScreen from './CreateAccountScreen';

describe('<CreateAccountScreen /> (screen 22)', () => {
  it('keeps the submit button disabled until the 18+ checkbox is checked', async () => {
    await renderWithProviders(<CreateAccountScreen />);
    fireEvent.changeText(screen.getByLabelText('Seu nome'), 'Ana');
    fireEvent.changeText(screen.getByLabelText('E-mail'), 'ana@example.com');
    fireEvent.changeText(screen.getByLabelText('Senha'), 'abcd1234');
    expect(screen.getByTestId('register-submit')).toBeDisabled();

    const adult = screen.getByRole('checkbox', { name: 'Tenho 18 anos ou mais.' });
    expect(adult).not.toBeChecked();
    fireEvent.press(adult);
    await waitFor(() =>
      expect(screen.getByRole('checkbox', { name: 'Tenho 18 anos ou mais.' })).toBeChecked(),
    );
    expect(screen.getByTestId('register-submit')).toBeEnabled();
  });
});
