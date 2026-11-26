import { fireEvent, screen } from '@testing-library/react-native';
import { router, useLocalSearchParams } from 'expo-router';

import { ApiError } from '@/api/client';
import { api } from '@/api/endpoints';
import { makeMeal } from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';

import EditMealScreen from './EditMealScreen';

jest.mock('@/api/endpoints', () => ({ api: { getMeal: jest.fn(), updateMeal: jest.fn() } }));

describe('<EditMealScreen /> (screen 26)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useLocalSearchParams as jest.Mock).mockReturnValue({ id: 'm1' });
    (api.getMeal as jest.Mock).mockResolvedValue(makeMeal());
  });

  it('states that points do not change and labels every control', async () => {
    await renderWithProviders(<EditMealScreen />);
    expect(
      await screen.findByText('A IA pode errar. Ajuste o que ela viu; os pontos não mudam.'),
    ).toBeOnTheScreen();
    expect(screen.getByRole('radio', { name: 'Almoço', checked: true })).toBeOnTheScreen();
    expect(screen.getByRole('radio', { name: 'Jantar', checked: false })).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Remover Arroz' })).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Voltar' })).toBeOnTheScreen();
  });

  it('saves the changed type and items, then goes back', async () => {
    (api.updateMeal as jest.Mock).mockResolvedValue(makeMeal({ meal_type: 'dinner' }));
    await renderWithProviders(<EditMealScreen />);
    await fireEvent.press(await screen.findByRole('radio', { name: 'Jantar' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Remover Feijão' }));
    await fireEvent.changeText(screen.getByTestId('edit-new-item'), 'Farofa');
    await fireEvent.press(screen.getByRole('button', { name: 'Adicionar item' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Salvar' }));
    expect(api.updateMeal).toHaveBeenCalledWith('m1', {
      meal_type: 'dinner',
      items: ['Arroz', 'Salada', 'Farofa'],
    });
    await screen.findByRole('button', { name: 'Salvar' });
    expect(router.back).toHaveBeenCalled();
  });

  it('disables Salvar with no items', async () => {
    await renderWithProviders(<EditMealScreen />);
    for (const item of ['Arroz', 'Feijão', 'Salada']) {
      await fireEvent.press(await screen.findByRole('button', { name: `Remover ${item}` }));
    }
    expect(screen.getByText('Deixe pelo menos um item.')).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Salvar' })).toBeDisabled();
  });

  it('shows a message when saving fails and stays on the screen', async () => {
    (api.updateMeal as jest.Mock).mockRejectedValue(new ApiError(500, 'UNKNOWN_ERROR', ''));
    await renderWithProviders(<EditMealScreen />);
    await fireEvent.press(await screen.findByRole('button', { name: 'Salvar' }));
    expect(await screen.findByText('Não deu para salvar. Tente de novo.')).toBeOnTheScreen();
    expect(router.back).not.toHaveBeenCalled();
  });

  it('shows the error state when the meal cannot be loaded', async () => {
    (api.getMeal as jest.Mock).mockRejectedValue(new ApiError(0, 'NETWORK_ERROR', ''));
    await renderWithProviders(<EditMealScreen />);
    expect(await screen.findByRole('button', { name: 'Tentar de novo' })).toBeOnTheScreen();
  });
});
