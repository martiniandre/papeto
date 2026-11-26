import { fireEvent, screen } from '@testing-library/react-native';
import { router } from 'expo-router';

import { useMealFlowStore } from '@/stores/mealFlow';
import { makeMeal, makePet } from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';

import ResultScreen, { confidenceLevel } from './ResultScreen';

jest.mock('./notificationsPrompt', () => ({ shouldAskForNotifications: jest.fn(async () => false) }));

describe('<ResultScreen /> (screen 6)', () => {
  const show = (meal = makeMeal()) =>
    useMealFlowStore.getState().setResult({ meal, pet: makePet(), events: [] });

  beforeEach(() => {
    jest.clearAllMocks();
    useMealFlowStore.getState().reset();
  });

  it('maps the confidence number to words', () => {
    expect(confidenceLevel(0.95)).toBe('high');
    expect(confidenceLevel(0.7)).toBe('medium');
    expect(confidenceLevel(0.3)).toBe('low');
  });

  it('opens "Sobre este prato" by default with the free part', async () => {
    show();
    await renderWithProviders(<ResultScreen />);
    expect(screen.getByTestId('about-toggle')).toBeExpanded();
    expect(screen.getByLabelText('cereais, no prato')).toBeOnTheScreen();
    expect(screen.getByLabelText('frutas, fora do prato')).toBeOnTheScreen();
    expect(screen.getByTestId('about-counts')).toHaveTextContent('3 itens · 3 cores');
    expect(screen.getByTestId('about-confidence')).toHaveTextContent('Confiança da leitura: alta');
    expect(screen.getByText('Grátis')).toBeOnTheScreen();
  });

  it('collapses and reopens the accordion with its state announced', async () => {
    show();
    await renderWithProviders(<ResultScreen />);
    await fireEvent.press(screen.getByTestId('about-toggle'));
    expect(screen.getByTestId('about-toggle')).toBeCollapsed();
    expect(screen.queryByTestId('about-content')).toBeNull();
    await fireEvent.press(screen.getByTestId('about-toggle'));
    expect(screen.getByTestId('about-content')).toBeOnTheScreen();
  });

  it('asks to check the items when the confidence is low', async () => {
    show(makeMeal({ confidence: 0.3 }));
    await renderWithProviders(<ResultScreen />);
    expect(screen.getByText('Não temos certeza de tudo. Confira os itens.')).toBeOnTheScreen();
  });

  it('announces "Seus hábitos" as locked, hides the blurred preview and opens the Premium placeholder', async () => {
    show();
    await renderWithProviders(<ResultScreen />);
    expect(screen.getByLabelText('Seus hábitos, bloqueado, disponível no Premium')).toBeOnTheScreen();
    expect(screen.getByTestId('habits-blurred', { includeHiddenElements: true })).toHaveProp(
      'importantForAccessibility',
      'no-hide-descendants',
    );
    await fireEvent.press(screen.getByRole('button', { name: 'Desbloquear seus hábitos' }));
    expect(router.push).toHaveBeenCalledWith('/premium');
  });

  it('shows a manual meal like any other, without food groups or confidence', async () => {
    show(
      makeMeal({
        source: 'manual',
        description: '',
        food_groups: [],
        colors: [],
        confidence: 1,
        items: ['Arroz', 'Ovo'],
      }),
    );
    await renderWithProviders(<ResultScreen />);
    expect(screen.getByText('• Arroz')).toBeOnTheScreen();
    expect(screen.queryByTestId('about-free')).toBeNull();
    expect(screen.queryByText(/limite|foto/i)).toBeNull();
  });

  it('goes home with the done button', async () => {
    show();
    await renderWithProviders(<ResultScreen />);
    await fireEvent.press(screen.getByTestId('result-done'));
    await screen.findByTestId('result-done');
    expect(router.replace).toHaveBeenCalledWith('/(tabs)/home');
  });
});
