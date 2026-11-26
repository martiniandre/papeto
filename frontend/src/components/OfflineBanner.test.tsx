import { onlineManager } from '@tanstack/react-query';
import { act, render, screen } from '@testing-library/react-native';

import { OfflineBanner } from './OfflineBanner';

describe('<OfflineBanner />', () => {
  afterEach(async () => { await act(() => onlineManager.setOnline(true)); });

  it('is hidden while online', async () => {
    await act(() => onlineManager.setOnline(true));
    await render(<OfflineBanner />);
    expect(screen.queryByTestId('offline-banner')).toBeNull();
  });

  it('shows the offline message as an alert', async () => {
    await act(() => onlineManager.setOnline(false));
    await render(<OfflineBanner />);
    expect(screen.getByRole('alert')).toBeOnTheScreen();
    expect(screen.getByText('Sem conexão. Tentamos de novo quando voltar.')).toBeOnTheScreen();
  });
});
