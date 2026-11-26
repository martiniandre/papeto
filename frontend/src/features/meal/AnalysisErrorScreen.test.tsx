import { onlineManager } from '@tanstack/react-query';
import { act, fireEvent, screen } from '@testing-library/react-native';
import { router, useLocalSearchParams } from 'expo-router';

import { useMealFlowStore } from '@/stores/mealFlow';
import { renderWithProviders } from '@/test/render';

import AnalysisErrorScreen, { parseReason } from './AnalysisErrorScreen';
import { discardPhoto } from './photo';

jest.mock('expo-image-picker', () => ({ launchImageLibraryAsync: jest.fn() }));
jest.mock('./photo', () => ({ resizePhoto: jest.fn(), discardPhoto: jest.fn() }));

describe('<AnalysisErrorScreen /> (screen 10)', () => {
  it.each([
    ['not_food', 'Parece que esta foto não é de um prato.'],
    ['unreadable', 'A foto ficou escura ou tremida.'],
    ['offline', 'Sem conexão.'],
    ['ai_error', 'Nosso analisador está com problemas agora.'],
  ])('shows its own text for %s and says it does not count', async (reason, text) => {
    (useLocalSearchParams as jest.Mock).mockReturnValue({ reason });
    await renderWithProviders(<AnalysisErrorScreen />);
    expect(screen.getByRole('alert')).toHaveTextContent(new RegExp(text));
    expect(screen.getByText('Esta tentativa não conta no limite de fotos do dia.')).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Tirar outra foto' })).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Escolher da galeria' })).toBeOnTheScreen();
  });

  it('offers manual entry that opens screen RF-95', async () => {
    (useLocalSearchParams as jest.Mock).mockReturnValue({ reason: 'unreadable' });
    await renderWithProviders(<AnalysisErrorScreen />);
    await fireEvent.press(screen.getByRole('button', { name: 'Escolher os alimentos' }));
    expect(router.replace).toHaveBeenCalledWith('/meal/manual');
  });

  describe('offline queue (memory only)', () => {
    beforeEach(() => {
      jest.clearAllMocks();
      onlineManager.setOnline(true);
      (useLocalSearchParams as jest.Mock).mockReturnValue({ reason: 'offline' });
      useMealFlowStore.getState().reset();
    });

    it('explains the queue and sends the waiting photo again', async () => {
      useMealFlowStore.getState().setPendingPhoto('file:///cache/p.jpg');
      await renderWithProviders(<AnalysisErrorScreen />);
      expect(screen.getByText('Sem conexão')).toBeOnTheScreen();
      expect(screen.getByText(/ela se perde/)).toBeOnTheScreen();
      await fireEvent.press(screen.getByRole('button', { name: 'Enviar a foto agora' }));
      expect(useMealFlowStore.getState().photoUri).toBe('file:///cache/p.jpg');
      expect(useMealFlowStore.getState().pendingPhotoUri).toBeNull();
      expect(router.replace).toHaveBeenCalledWith('/meal/analyzing');
    });

    it('retries by itself when the connection comes back', async () => {
      useMealFlowStore.getState().setPendingPhoto('file:///cache/p.jpg');
      await act(async () => onlineManager.setOnline(false));
      await renderWithProviders(<AnalysisErrorScreen />);
      expect(screen.getByRole('button', { name: 'Enviar a foto agora' })).toBeDisabled();
      await act(async () => onlineManager.setOnline(true));
      expect(router.replace).toHaveBeenCalledWith('/meal/analyzing');
      expect(useMealFlowStore.getState().photoUri).toBe('file:///cache/p.jpg');
    });

    it('drops the waiting photo when the user takes another way out', async () => {
      useMealFlowStore.getState().setPendingPhoto('file:///cache/p.jpg');
      await renderWithProviders(<AnalysisErrorScreen />);
      await fireEvent.press(screen.getByRole('button', { name: 'Tirar outra foto' }));
      expect(discardPhoto).toHaveBeenCalledWith('file:///cache/p.jpg');
      expect(useMealFlowStore.getState().pendingPhotoUri).toBeNull();
    });

    it('does not show the queue when nothing is waiting', async () => {
      await renderWithProviders(<AnalysisErrorScreen />);
      expect(screen.queryByTestId('offline-queue')).toBeNull();
    });
  });

  it('treats unknown reasons as AI errors', async () => {
    expect(parseReason('weird')).toBe('ai_error');
    expect(parseReason(undefined)).toBe('ai_error');
  });
});
