import { act, fireEvent, screen } from '@testing-library/react-native';
import { router } from 'expo-router';

import { api } from '@/api/endpoints';
import HomeScreen from '@/features/home/HomeScreen';
import PremiumPlaceholderScreen from '@/features/premium/PremiumPlaceholderScreen';
import { usePetAlertStore } from '@/stores/petAlerts';
import { makePet } from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';

import { FaintedScreen, LifeLostScreen } from './PetAlertScreens';

jest.mock('@/api/endpoints', () => ({ api: { getPet: jest.fn() } }));
jest.mock('expo-camera', () => ({
  Camera: { getCameraPermissionsAsync: jest.fn(async () => ({ granted: true })) },
}));
jest.setTimeout(30000);

describe('pet alerts (flow 6)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    usePetAlertStore.setState({ lifeLostPending: false, faintedShown: false });
  });

  describe('Home opening', () => {
    it('opens "lost a life" (28) on the life_lost event', async () => {
      (api.getPet as jest.Mock).mockResolvedValue(makePet({ lives: 1, mood: 'sleepy', events: ['life_lost'] }));
      await renderWithProviders(<HomeScreen />);
      await screen.findByLabelText('Pipoca, com sono');
      expect(router.push).toHaveBeenCalledWith('/pet/life-lost');
    });

    it('opens "fainted" (12) once for mood fainted, not on every refresh', async () => {
      (api.getPet as jest.Mock).mockResolvedValue(makePet({ lives: 0, mood: 'fainted' }));
      const { queryClient } = await renderWithProviders(<HomeScreen />);
      await screen.findByLabelText('Pipoca, desmaiado');
      expect(router.push).toHaveBeenCalledWith('/pet/fainted');
      await act(async () => {
        await queryClient.refetchQueries({ queryKey: ['pet'] });
      });
      expect(router.push).toHaveBeenCalledTimes(1);
    });

    it('shows only "fainted" when 0 lives come with life_lost', async () => {
      (api.getPet as jest.Mock).mockResolvedValue(
        makePet({ lives: 0, mood: 'fainted', events: ['life_lost'] }),
      );
      await renderWithProviders(<HomeScreen />);
      await screen.findByLabelText('Pipoca, desmaiado');
      expect(router.push).toHaveBeenCalledTimes(1);
      expect(router.push).toHaveBeenCalledWith('/pet/fainted');
    });

    it('does not show Home while the pet has no name (screen 43 takes over)', async () => {
      (api.getPet as jest.Mock).mockResolvedValue(makePet({ name: null }));
      await renderWithProviders(<HomeScreen />);
      await act(async () => {});
      expect(screen.queryByTestId('log-meal')).toBeNull();
      expect(router.push).not.toHaveBeenCalled();
    });

    it('shows nothing extra for a happy pet', async () => {
      (api.getPet as jest.Mock).mockResolvedValue(makePet({ mood: 'happy' }));
      await renderWithProviders(<HomeScreen />);
      await screen.findByLabelText('Pipoca, feliz');
      expect(router.push).not.toHaveBeenCalled();
    });
  });

  describe('<LifeLostScreen /> (28)', () => {
    it('renders lives from the API and labelled actions', async () => {
      (api.getPet as jest.Mock).mockResolvedValue(makePet({ lives: 2, mood: 'tired' }));
      await renderWithProviders(<LifeLostScreen />);
      expect(await screen.findByText('Pipoca perdeu uma vida')).toBeOnTheScreen();
      expect(
        screen.getByText('Um dia ficou sem registro. Ainda restam 2 vidas, e uma foto hoje deixa Pipoca animado de novo.'),
      ).toBeOnTheScreen();
      expect(screen.getByRole('button', { name: 'Registrar uma refeição' })).toBeOnTheScreen();
      await fireEvent.press(screen.getByRole('button', { name: 'Vai ficar fora? Pause o pet, Premium' }));
      expect(router.push).toHaveBeenCalledWith('/premium');
    });

    it('goes Home and starts the log', async () => {
      (api.getPet as jest.Mock).mockResolvedValue(makePet());
      await renderWithProviders(<LifeLostScreen />);
      await fireEvent.press(await screen.findByRole('button', { name: 'Registrar uma refeição' }));
      await act(async () => {});
      expect(router.replace).toHaveBeenCalledWith('/(tabs)/home');
      expect(router.push).toHaveBeenCalledWith('/meal/camera');
    });

    it('shows loading and error states', async () => {
      (api.getPet as jest.Mock).mockReturnValue(new Promise(() => undefined));
      await renderWithProviders(<LifeLostScreen />);
      expect(screen.getByLabelText('Carregando')).toBeOnTheScreen();
    });
  });

  describe('<FaintedScreen /> (12)', () => {
    it('reassures and opens the Premium placeholder from Pause', async () => {
      (api.getPet as jest.Mock).mockResolvedValue(makePet({ lives: 0, mood: 'fainted' }));
      await renderWithProviders(<FaintedScreen />);
      expect(await screen.findByText('Pipoca desmaiou, mas está tudo bem')).toBeOnTheScreen();
      expect(screen.getByRole('button', { name: 'Acordar com uma refeição' })).toBeOnTheScreen();
      await fireEvent.press(screen.getByRole('button', { name: 'Pausar por uns dias, Premium' }));
      expect(router.push).toHaveBeenCalledWith('/premium');
    });
  });

  describe('<PremiumPlaceholderScreen />', () => {
    it('explains that Premium is coming and closes', async () => {
      await renderWithProviders(<PremiumPlaceholderScreen />);
      expect(screen.getByText('Papeto Premium')).toBeOnTheScreen();
      await fireEvent.press(screen.getByRole('button', { name: 'Voltar' }));
      expect(router.back).toHaveBeenCalled();
    });
  });
});
