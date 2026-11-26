import { fireEvent, screen } from '@testing-library/react-native';
import { router, useLocalSearchParams } from 'expo-router';

import { ApiError } from '@/api/client';
import { api } from '@/api/endpoints';
import { makeMeal } from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';

import MealDetailScreen from './MealDetailScreen';
import { undoMealDelete, usePendingDeleteStore } from './pendingDelete';

jest.mock('@/api/endpoints', () => ({ api: { getMeal: jest.fn(), deleteMeal: jest.fn() } }));

// The first render in a cold Jest worker can be slow on loaded machines.
jest.setTimeout(30000);

describe('<MealDetailScreen /> (screens 25 and 37)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    undoMealDelete();
    (useLocalSearchParams as jest.Mock).mockReturnValue({ id: 'm1' });
  });

  it('shows the loading skeleton first', async () => {
    (api.getMeal as jest.Mock).mockReturnValue(new Promise(() => undefined));
    await renderWithProviders(<MealDetailScreen />);
    expect(screen.getByLabelText('Carregando')).toBeOnTheScreen();
  });

  it('shows the error state with retry', async () => {
    (api.getMeal as jest.Mock).mockRejectedValue(new ApiError(404, 'MEAL_NOT_FOUND', ''));
    await renderWithProviders(<MealDetailScreen />);
    expect(await screen.findByText('Esta refeição não está mais no histórico.')).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Tentar de novo' })).toBeOnTheScreen();
  });

  it('renders the meal with labelled actions and no points or scores', async () => {
    (api.getMeal as jest.Mock).mockResolvedValue(makeMeal());
    await renderWithProviders(<MealDetailScreen />);
    expect(await screen.findByText('Um prato colorido com arroz, feijão e salada.')).toBeOnTheScreen();
    expect(screen.getByText('A foto foi apagada após a avaliação')).toBeOnTheScreen();
    expect(screen.getByText('3 itens · 3 cores')).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Voltar' })).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Corrigir' })).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Apagar' })).toBeOnTheScreen();
    expect(screen.queryByText(/ponto/i)).toBeNull();
  });

  it('opens the correction screen', async () => {
    (api.getMeal as jest.Mock).mockResolvedValue(makeMeal());
    await renderWithProviders(<MealDetailScreen />);
    await fireEvent.press(await screen.findByRole('button', { name: 'Corrigir' }));
    expect(router.push).toHaveBeenCalledWith('/meals/m1/edit');
  });

  it('confirms in a sheet with neutral copy, then hides the meal and waits (no DELETE yet)', async () => {
    (api.getMeal as jest.Mock).mockResolvedValue(makeMeal());
    await renderWithProviders(<MealDetailScreen />);
    await fireEvent.press(await screen.findByRole('button', { name: 'Apagar' }));
    expect(
      await screen.findByText('A refeição sai do seu histórico. Pontos e vidas não mudam.'),
    ).toBeOnTheScreen();
    expect(screen.queryByText(/saem do total/i)).toBeNull();
    await fireEvent.press(screen.getByRole('button', { name: 'Apagar refeição' }));
    expect(usePendingDeleteStore.getState().pendingId).toBe('m1');
    expect(router.dismissTo).toHaveBeenCalledWith('/(tabs)/history');
    expect(api.deleteMeal).not.toHaveBeenCalled();
    undoMealDelete();
  });

  it('keeps the meal when the user taps "Manter"', async () => {
    (api.getMeal as jest.Mock).mockResolvedValue(makeMeal());
    await renderWithProviders(<MealDetailScreen />);
    await fireEvent.press(await screen.findByRole('button', { name: 'Apagar' }));
    await fireEvent.press(await screen.findByRole('button', { name: 'Manter' }));
    expect(usePendingDeleteStore.getState().pendingId).toBeNull();
    expect(router.dismissTo).not.toHaveBeenCalled();
  });
});
