import { render, screen } from '@testing-library/react-native';

import { Hearts } from './Hearts';
import { PointsBadge } from './PointsBadge';

describe('<Hearts />', () => {
  it('announces lives as text, not only as shapes', async () => {
    await render(<Hearts lives={2} max={4} />);
    expect(screen.getByLabelText('2 de 4 vidas')).toBeOnTheScreen();
  });

  it('draws full and empty hearts from the API values', async () => {
    await render(<Hearts lives={1} max={4} />);
    expect(screen.getAllByTestId('heart-full')).toHaveLength(1);
    expect(screen.getAllByTestId('heart-empty')).toHaveLength(3);
  });
});

describe('<PointsBadge />', () => {
  it('pluralizes points', async () => {
    const { rerender } = await render(<PointsBadge points={1} />);
    expect(screen.getByLabelText('1 ponto')).toBeOnTheScreen();
    await rerender(<PointsBadge points={20} />);
    expect(screen.getByLabelText('20 pontos')).toBeOnTheScreen();
  });
});
