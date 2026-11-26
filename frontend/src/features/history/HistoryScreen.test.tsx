import { QueryClient } from '@tanstack/react-query';
import { act, fireEvent, screen } from '@testing-library/react-native';
import { router } from 'expo-router';

import { api } from '@/api/endpoints';
import { makeMeal } from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';

import HistoryScreen from './HistoryScreen';
import { UNDO_WINDOW_MS, scheduleMealDelete, undoMealDelete } from './pendingDelete';

jest.mock('@/api/endpoints', () => ({ api: { listMeals: jest.fn(), deleteMeal: jest.fn() } }));
jest.mock('expo-camera', () => ({
  Camera: { getCameraPermissionsAsync: jest.fn(async () => ({ granted: false })) },
}));

// The first render in a cold Jest worker can be slow on loaded machines.
jest.setTimeout(30000);

const page = (...ids: string[]) => ({
  items: ids.map((id) => makeMeal({ id, description: `Prato ${id}` })),
  next_cursor: null,
});

describe('<HistoryScreen /> (screens 7, 14 and 42)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    undoMealDelete();
  });

  it('shows the empty state (14) with a log button', async () => {
    (api.listMeals as jest.Mock).mockResolvedValue(page());
    await renderWithProviders(<HistoryScreen />);
    expect(await screen.findByText('Nenhuma refeição ainda')).toBeOnTheScreen();
    expect(screen.getByText('Sua primeira foto aparece aqui.')).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Registrar refeição' })).toBeOnTheScreen();
  });

  it('opens the meal detail from a card', async () => {
    (api.listMeals as jest.Mock).mockResolvedValue(page('a'));
    await renderWithProviders(<HistoryScreen />);
    await fireEvent.press(await screen.findByTestId('meal-card'));
    expect(router.push).toHaveBeenCalledWith('/meals/a');
  });

  describe('delete with undo', () => {
    beforeEach(() => jest.useFakeTimers());
    afterEach(() => jest.useRealTimers());

    const setup = async () => {
      (api.listMeals as jest.Mock).mockResolvedValue(page('a', 'b'));
      (api.deleteMeal as jest.Mock).mockResolvedValue(undefined);
      const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
      await renderWithProviders(<HistoryScreen />, client);
      expect(await screen.findByText('Prato a')).toBeOnTheScreen();
      return client;
    };

    it('shows "Refeição apagada" + Desfazer, and undo restores the meal without calling the API', async () => {
      const client = await setup();
      await act(async () => scheduleMealDelete('a', client));
      expect(screen.getByText('Refeição apagada')).toBeOnTheScreen();
      expect(screen.queryByText('Prato a')).toBeNull();
      expect(screen.getByText('Prato b')).toBeOnTheScreen();

      await fireEvent.press(screen.getByRole('button', { name: 'Desfazer' }));
      expect(screen.queryByText('Refeição apagada')).toBeNull();
      expect(screen.getByText('Prato a')).toBeOnTheScreen();

      await act(async () => {
        jest.advanceTimersByTime(UNDO_WINDOW_MS + 100);
      });
      expect(api.deleteMeal).not.toHaveBeenCalled();
    });

    it('calls DELETE only after 5 seconds without undo', async () => {
      const client = await setup();
      await act(async () => scheduleMealDelete('a', client));
      await act(async () => {
        jest.advanceTimersByTime(UNDO_WINDOW_MS - 100);
      });
      expect(api.deleteMeal).not.toHaveBeenCalled();
      await act(async () => {
        jest.advanceTimersByTime(200);
      });
      expect(api.deleteMeal).toHaveBeenCalledWith('a');
      expect(screen.queryByText('Refeição apagada')).toBeNull();
    });

    it('sends the previous DELETE right away when a second meal is deleted', async () => {
      const client = await setup();
      await act(async () => scheduleMealDelete('a', client));
      await act(async () => scheduleMealDelete('b', client));
      expect(api.deleteMeal).toHaveBeenCalledWith('a');
      expect(api.deleteMeal).not.toHaveBeenCalledWith('b');
      undoMealDelete();
    });

    it('brings the meal back with a message when DELETE fails', async () => {
      const client = await setup();
      (api.deleteMeal as jest.Mock).mockRejectedValue(new Error('boom'));
      await act(async () => scheduleMealDelete('a', client));
      await act(async () => {
        jest.advanceTimersByTime(UNDO_WINDOW_MS + 100);
      });
      expect(await screen.findByTestId('delete-failed')).toBeOnTheScreen();
    });
  });
});
