import { fireEvent, render, screen } from '@testing-library/react-native';

import { ApiError, NETWORK_ERROR } from '@/api/client';

import { ErrorState } from './ErrorState';
import { Skeleton } from './Skeleton';

describe('<ErrorState />', () => {
  it('translates the API error code and retries', async () => {
    const onRetry = jest.fn();
    await render(<ErrorState error={new ApiError(503, 'VISION_UNAVAILABLE', 'x')} onRetry={onRetry} />);
    expect(screen.getByText('Nosso analisador está com problemas agora.')).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Tentar de novo' }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('shows the offline text for network errors', async () => {
    await render(<ErrorState error={new ApiError(0, NETWORK_ERROR, 'x')} onRetry={jest.fn()} />);
    expect(screen.getByText('Sem conexão. Tentamos de novo quando voltar.')).toBeOnTheScreen();
  });

  it('falls back to a generic message for unknown errors', async () => {
    await render(<ErrorState error={new Error('boom')} onRetry={jest.fn()} />);
    expect(screen.getByText('Algo deu errado do nosso lado.')).toBeOnTheScreen();
  });
});

describe('<Skeleton />', () => {
  it('is announced as loading', async () => {
    await render(<Skeleton />);
    expect(screen.getByLabelText('Carregando')).toBeOnTheScreen();
  });
});
