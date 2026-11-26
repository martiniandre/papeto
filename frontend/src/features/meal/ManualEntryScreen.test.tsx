import { fireEvent, screen } from '@testing-library/react-native';
import { router } from 'expo-router';

import { ApiError } from '@/api/client';
import { api } from '@/api/endpoints';
import { useMealFlowStore } from '@/stores/mealFlow';
import { makeMeal, makePet } from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';

import ManualEntryScreen, { guessMealType } from './ManualEntryScreen';

jest.mock('@/api/endpoints', () => ({ api: { createManualMeal: jest.fn() } }));
jest.setTimeout(30000);

describe('<ManualEntryScreen /> (RF-95)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useMealFlowStore.getState().reset();
  });

  it('guesses the meal type from the hour', () => {
    expect(guessMealType(new Date(2026, 0, 1, 8))).toBe('breakfast');
    expect(guessMealType(new Date(2026, 0, 1, 12))).toBe('lunch');
    expect(guessMealType(new Date(2026, 0, 1, 16))).toBe('snack');
    expect(guessMealType(new Date(2026, 0, 1, 20))).toBe('dinner');
  });

  it('keeps the submit disabled until a food is chosen and never mentions the photo limit', async () => {
    await renderWithProviders(<ManualEntryScreen />);
    expect(screen.getByRole('button', { name: 'Registrar refeição' })).toBeDisabled();
    expect(screen.getByText('Escolha pelo menos um alimento.')).toBeOnTheScreen();
    expect(screen.queryByText(/limite|fotos de hoje/i)).toBeNull();
  });

  it('sends the chosen items and type and opens the normal result screen', async () => {
    const created = { meal: makeMeal({ source: 'manual' }), pet: makePet(), events: [] };
    (api.createManualMeal as jest.Mock).mockResolvedValue(created);
    await renderWithProviders(<ManualEntryScreen />);

    await fireEvent.press(screen.getByRole('radio', { name: 'Jantar' }));
    expect(screen.getByRole('radio', { name: 'Jantar' })).toBeSelected();
    await fireEvent.press(screen.getByRole('checkbox', { name: 'Arroz' }));
    expect(screen.getByRole('checkbox', { name: 'Arroz' })).toBeChecked();
    await fireEvent.changeText(screen.getByLabelText('Outro alimento'), 'Mandioca');
    await fireEvent.press(screen.getByRole('button', { name: 'Adicionar alimento' }));
    expect(screen.getByRole('button', { name: 'Remover Mandioca' })).toBeOnTheScreen();

    await fireEvent.press(screen.getByRole('button', { name: 'Registrar refeição' }));
    await screen.findByRole('button', { name: 'Registrar refeição' });
    expect(api.createManualMeal).toHaveBeenCalledWith({ items: ['Arroz', 'Mandioca'], meal_type: 'dinner' });
    expect(useMealFlowStore.getState().result).toEqual(created);
    expect(router.replace).toHaveBeenCalledWith('/meal/result');
  });

  it('shows a message when saving fails and stays on the screen', async () => {
    (api.createManualMeal as jest.Mock).mockRejectedValue(new ApiError(500, 'UNKNOWN_ERROR', ''));
    await renderWithProviders(<ManualEntryScreen />);
    await fireEvent.press(screen.getByRole('checkbox', { name: 'Ovo' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Registrar refeição' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/Não deu para registrar agora/);
    expect(router.replace).not.toHaveBeenCalledWith('/meal/result');
  });

  it('sends the user to consent when the meal-data consent is missing', async () => {
    (api.createManualMeal as jest.Mock).mockRejectedValue(new ApiError(403, 'MEAL_CONSENT_REQUIRED', ''));
    await renderWithProviders(<ManualEntryScreen />);
    await fireEvent.press(screen.getByRole('checkbox', { name: 'Ovo' }));
    await fireEvent.press(screen.getByRole('button', { name: 'Registrar refeição' }));
    await screen.findByRole('alert');
    expect(router.replace).toHaveBeenCalledWith('/(onboarding)/age-terms');
  });

  it('has a labelled back button', async () => {
    await renderWithProviders(<ManualEntryScreen />);
    await fireEvent.press(screen.getByRole('button', { name: 'Voltar' }));
    expect(router.replace).toHaveBeenCalledWith('/(tabs)/home');
  });
});
