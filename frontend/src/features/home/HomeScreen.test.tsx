import { act, fireEvent, screen } from '@testing-library/react-native';
import { router } from 'expo-router';
import { Linking } from 'react-native';

import { ApiError } from '@/api/client';
import { api } from '@/api/endpoints';
import type { Pet } from '@/api/types';
import { useMealFlowStore } from '@/stores/mealFlow';
import { renderWithProviders } from '@/test/render';

import HomeScreen from './HomeScreen';

jest.mock('@/api/endpoints', () => ({ api: { getPet: jest.fn() } }));
jest.mock('expo-camera', () => ({
  Camera: { getCameraPermissionsAsync: jest.fn(async () => ({ granted: false })) },
}));

const pet = (overrides: Partial<Pet> = {}): Pet => ({
  name: 'Pipoca',
  color: 'mint',
  lives: 2,
  max_lives: 4,
  streak_days: 3,
  points: 40,
  mood: 'tired',
  events: [],
  support_hint: false,
  level: 1,
  level_progress: { points: 40, current_level_at: 0, next_level_at: 100 },
  attributes: { strength: 0, speed: 0, skill: 0, endurance: 0, intelligence: 0 },
  unspent_attribute_points: 0,
  ...overrides,
});

describe('<HomeScreen /> (screen 3)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useMealFlowStore.setState({ limitReachedOn: null });
  });

  it('shows the loading skeleton first', async () => {
    (api.getPet as jest.Mock).mockReturnValue(new Promise(() => undefined));
    await renderWithProviders(<HomeScreen />);
    expect(screen.getByLabelText('Carregando')).toBeOnTheScreen();
  });

  it('renders mood, lives and points exactly as the API returns', async () => {
    (api.getPet as jest.Mock).mockResolvedValue(pet({ mood: 'sleepy', lives: 1 }));
    await renderWithProviders(<HomeScreen />);
    expect(await screen.findByLabelText('Pipoca, com sono')).toBeOnTheScreen();
    expect(screen.getByLabelText('1 de 4 vidas')).toBeOnTheScreen();
    expect(screen.getByLabelText('40 pontos')).toBeOnTheScreen();
    expect(screen.getByText('3 dias seguidos')).toBeOnTheScreen();
  });

  it('shows the error state with retry', async () => {
    (api.getPet as jest.Mock).mockRejectedValue(new ApiError(500, 'UNKNOWN_ERROR', ''));
    await renderWithProviders(<HomeScreen />);
    expect(await screen.findByRole('button', { name: 'Tentar de novo' })).toBeOnTheScreen();
  });

  it('opens camera permission on first log', async () => {
    (api.getPet as jest.Mock).mockResolvedValue(pet());
    await renderWithProviders(<HomeScreen />);
    await fireEvent.press(await screen.findByRole('button', { name: 'Registrar refeição' }));
    await act(async () => {});
    expect(router.push).toHaveBeenCalledWith('/meal/camera-permission');
  });

  it('goes to Daily limit when the photos are used up today', async () => {
    useMealFlowStore.getState().markLimitReached();
    (api.getPet as jest.Mock).mockResolvedValue(pet({ mood: 'happy' }));
    await renderWithProviders(<HomeScreen />);
    expect(await screen.findByTestId('photos-used-up')).toBeOnTheScreen();
    expect(screen.getByText('2 de 2 fotos com IA hoje · voltam à meia-noite')).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Registrar refeição' }));
    await act(async () => {});
    expect(router.push).toHaveBeenCalledWith('/meal/daily-limit');
  });

  describe('level and attributes', () => {
    it('renders the level and progress exactly as the API returns them', async () => {
      (api.getPet as jest.Mock).mockResolvedValue(
        pet({ level: 3, points: 250, level_progress: { points: 250, current_level_at: 200, next_level_at: 300 } }),
      );
      await renderWithProviders(<HomeScreen />);
      expect(await screen.findByText('Nível 3')).toBeOnTheScreen();
      expect(screen.getByText('250 de 300 pontos para o próximo nível')).toBeOnTheScreen();
      const bar = screen.getByTestId('level-progress-bar');
      expect(bar.props.accessibilityRole).toBe('progressbar');
      expect(bar.props.accessibilityValue).toEqual({ min: 0, max: 100, now: 50 });
    });

    it('shows a quiet attributes entry when no points are unspent', async () => {
      (api.getPet as jest.Mock).mockResolvedValue(pet());
      await renderWithProviders(<HomeScreen />);
      expect(await screen.findByLabelText('Atributos')).toBeOnTheScreen();
      expect(screen.queryByTestId('unspent-points')).toBeNull();
    });

    it('highlights the entry with the unspent count and opens the attributes screen', async () => {
      (api.getPet as jest.Mock).mockResolvedValue(pet({ unspent_attribute_points: 2 }));
      await renderWithProviders(<HomeScreen />);
      expect(await screen.findByText('2 pontos para distribuir')).toBeOnTheScreen();
      await fireEvent.press(screen.getByLabelText('Atributos, 2 pontos para distribuir'));
      expect(router.push).toHaveBeenCalledWith('/attributes');
    });

    it('celebrates the level_up event', async () => {
      (api.getPet as jest.Mock).mockResolvedValue(pet({ level: 2, events: ['level_up'] }));
      await renderWithProviders(<HomeScreen />);
      expect(await screen.findByText('Subiu para o nível 2!')).toBeOnTheScreen();
    });
  });

  describe('support card', () => {
    it('is hidden by default', async () => {
      (api.getPet as jest.Mock).mockResolvedValue(pet());
      await renderWithProviders(<HomeScreen />);
      await screen.findByTestId('mood-message');
      expect(screen.queryByTestId('support-card')).toBeNull();
    });

    it('shows a kind card with the CVV path when support_hint is true', async () => {
      (api.getPet as jest.Mock).mockResolvedValue(pet({ support_hint: true }));
      const open = jest.spyOn(Linking, 'openURL').mockResolvedValue();
      await renderWithProviders(<HomeScreen />);
      expect(await screen.findByTestId('support-card')).toBeOnTheScreen();
      expect(screen.getByText('Tudo bem por aí?')).toBeOnTheScreen();
      expect(screen.getByText(/Sem cobrança/)).toBeOnTheScreen();
      await fireEvent.press(screen.getByRole('button', { name: 'Ligar para o CVV, telefone 188' }));
      expect(open).toHaveBeenCalledWith('tel:188');
      await fireEvent.press(screen.getByRole('button', { name: 'Abrir o site do CVV, cvv.org.br' }));
      expect(open).toHaveBeenCalledWith('https://cvv.org.br');
    });
  });
});
