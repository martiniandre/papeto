import { screen } from '@testing-library/react-native';
import { useLocalSearchParams } from 'expo-router';

import { renderWithProviders } from '@/test/render';

import AnalysisErrorScreen, { parseReason } from './AnalysisErrorScreen';

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

  it('treats unknown reasons as AI errors', async () => {
    expect(parseReason('weird')).toBe('ai_error');
    expect(parseReason(undefined)).toBe('ai_error');
  });
});
