import { fireEvent, screen, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';

import { api } from '@/api/endpoints';
import { renderWithProviders } from '@/test/render';

import NamePetScreen from './NamePetScreen';

jest.mock('@/api/endpoints', () => ({
  api: { updatePet: jest.fn(async (input: { name: string }) => ({ name: input.name })) },
}));

describe('<NamePetScreen /> (screen 43)', () => {
  beforeEach(() => jest.clearAllMocks());

  it('keeps Continue disabled while the name is empty', async () => {
    await renderWithProviders(<NamePetScreen />);
    expect(screen.getByTestId('name-continue')).toBeDisabled();
    await fireEvent.changeText(screen.getByLabelText('Nome do bichinho'), 'Nino');
    expect(screen.getByTestId('name-continue')).toBeEnabled();
  });

  it('limits the input to 20 characters', async () => {
    await renderWithProviders(<NamePetScreen />);
    expect(screen.getByLabelText('Nome do bichinho').props.maxLength).toBe(20);
  });

  it('offers three suggestions and marks the chosen one as selected', async () => {
    await renderWithProviders(<NamePetScreen />);
    expect(screen.getByTestId('suggestion-Bolinha')).toBeOnTheScreen();
    expect(screen.getByTestId('suggestion-Pipoca')).toBeOnTheScreen();
    expect(screen.getByTestId('suggestion-Biscoito')).toBeOnTheScreen();

    await fireEvent.press(screen.getByTestId('suggestion-Pipoca'));
    expect(screen.getByTestId('suggestion-Pipoca')).toBeSelected();
    expect(screen.getByLabelText('Pipoca, selecionado')).toBeOnTheScreen();
  });

  it('saves the trimmed name and moves to Meet your pet', async () => {
    await renderWithProviders(<NamePetScreen />);
    await fireEvent.changeText(screen.getByLabelText('Nome do bichinho'), '  Nino ');
    await fireEvent.press(screen.getByTestId('name-continue'));
    await waitFor(() => expect(router.replace).toHaveBeenCalledWith('/(onboarding)/meet-pet'));
    expect(api.updatePet).toHaveBeenCalledWith({ name: 'Nino' });
  });
});
