import { act, fireEvent, screen, waitFor } from '@testing-library/react-native';

import { ApiError } from '@/api/client';
import { api } from '@/api/endpoints';
import { makePet } from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';

import AttributesScreen from './AttributesScreen';

jest.mock('@/api/endpoints', () => ({ api: { getPet: jest.fn(), spendAttributes: jest.fn() } }));

const press = async (id: string) => {
  await act(async () => {
    fireEvent.press(screen.getByTestId(id));
  });
};

describe('<AttributesScreen />', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getPet as jest.Mock).mockResolvedValue(
      makePet({ level: 2, unspent_attribute_points: 3, attributes: { strength: 1, speed: 0, skill: 0, endurance: 0, intelligence: 0 } }),
    );
  });

  it('shows the loading skeleton first', async () => {
    (api.getPet as jest.Mock).mockReturnValueOnce(new Promise(() => undefined));
    await renderWithProviders(<AttributesScreen />);
    expect(screen.getByLabelText('Carregando')).toBeOnTheScreen();
  });

  it('lists the five attributes and the unspent points from the API', async () => {
    await renderWithProviders(<AttributesScreen />);
    for (const label of ['Força', 'Velocidade', 'Habilidade', 'Resistência', 'Inteligência']) {
      expect(await screen.findByText(label)).toBeOnTheScreen();
    }
    expect(screen.getByLabelText('3 pontos para distribuir')).toBeOnTheScreen();
    expect(screen.getByLabelText('Força: 1')).toBeOnTheScreen();
    expect(screen.getByText(/não dá para desfazer/i)).toBeOnTheScreen();
  });

  it('labels the steppers for screen readers', async () => {
    await renderWithProviders(<AttributesScreen />);
    expect(await screen.findByLabelText('Aumentar Força')).toBeOnTheScreen();
    expect(screen.getByLabelText('Diminuir Força')).toBeOnTheScreen();
  });

  it('never lets the user allocate more than the unspent points', async () => {
    await renderWithProviders(<AttributesScreen />);
    await screen.findByText('Força');
    await press('increase-strength');
    await press('increase-strength');
    await press('increase-speed');
    expect(screen.getByLabelText('0 ponto para distribuir')).toBeOnTheScreen();
    expect(screen.getByLabelText('Força: 3')).toBeOnTheScreen();
    expect(screen.getByLabelText('Aumentar Habilidade')).toBeDisabled();
    await press('increase-skill');
    expect(screen.getByLabelText('Habilidade: 0')).toBeOnTheScreen();
  });

  it('never goes below the points already spent', async () => {
    await renderWithProviders(<AttributesScreen />);
    await screen.findByText('Força');
    expect(screen.getByLabelText('Diminuir Força')).toBeDisabled();
    await press('increase-strength');
    await press('decrease-strength');
    await press('decrease-strength');
    expect(screen.getByLabelText('Força: 1')).toBeOnTheScreen();
    expect(screen.getByLabelText('3 pontos para distribuir')).toBeOnTheScreen();
  });

  it('keeps confirm disabled until something is allocated', async () => {
    await renderWithProviders(<AttributesScreen />);
    await screen.findByText('Força');
    expect(screen.getByRole('button', { name: 'Distribuir pontos' })).toBeDisabled();
    await press('increase-skill');
    expect(screen.getByRole('button', { name: 'Distribuir pontos' })).toBeEnabled();
  });

  it('asks to confirm, then sends only the raised attributes and shows success', async () => {
    (api.spendAttributes as jest.Mock).mockResolvedValue(
      makePet({ level: 2, unspent_attribute_points: 1, attributes: { strength: 1, speed: 0, skill: 2, endurance: 0, intelligence: 0 } }),
    );
    await renderWithProviders(<AttributesScreen />);
    await screen.findByText('Força');
    await press('increase-skill');
    await press('increase-skill');
    await press('spend-attributes');

    expect(screen.getByText('Confirmar a distribuição?')).toBeOnTheScreen();
    expect(api.spendAttributes).not.toHaveBeenCalled();

    await press('confirm-spend-yes');
    await waitFor(() => expect(api.spendAttributes).toHaveBeenCalledWith({ skill: 2 }));
    expect(await screen.findByTestId('spend-success')).toBeOnTheScreen();
    expect(screen.getByLabelText('Habilidade: 2')).toBeOnTheScreen();
    expect(screen.getByLabelText('1 ponto para distribuir')).toBeOnTheScreen();
  });

  it('goes back from the confirmation without spending', async () => {
    await renderWithProviders(<AttributesScreen />);
    await screen.findByText('Força');
    await press('increase-skill');
    await press('spend-attributes');
    await fireEvent.press(screen.getByRole('button', { name: 'Voltar e revisar' }));
    expect(screen.queryByTestId('confirm-spend')).toBeNull();
    expect(api.spendAttributes).not.toHaveBeenCalled();
  });

  it('refetches the pet and explains when the points are not enough', async () => {
    (api.spendAttributes as jest.Mock).mockRejectedValue(
      new ApiError(400, 'NOT_ENOUGH_ATTRIBUTE_POINTS', 'x'),
    );
    await renderWithProviders(<AttributesScreen />);
    await screen.findByText('Força');
    await press('increase-skill');
    await press('spend-attributes');
    (api.getPet as jest.Mock).mockResolvedValue(makePet({ level: 2, unspent_attribute_points: 0 }));
    await press('confirm-spend-yes');

    expect(await screen.findByText(/Seus pontos mudaram/)).toBeOnTheScreen();
    await waitFor(() => expect(api.getPet).toHaveBeenCalledTimes(2));
    expect(await screen.findByLabelText('0 ponto para distribuir')).toBeOnTheScreen();
    expect(screen.getByLabelText('Habilidade: 0')).toBeOnTheScreen();
    expect(screen.getByTestId('no-points')).toBeOnTheScreen();
  });

  it('shows the offline message when the request cannot reach the server', async () => {
    (api.spendAttributes as jest.Mock).mockRejectedValue(new ApiError(0, 'NETWORK_ERROR', ''));
    await renderWithProviders(<AttributesScreen />);
    await screen.findByText('Força');
    await press('increase-speed');
    await press('spend-attributes');
    await press('confirm-spend-yes');
    expect(await screen.findByText(/Sem conexão/)).toBeOnTheScreen();
    expect(screen.getByLabelText('Velocidade: 0')).toBeOnTheScreen();
  });

  it('shows the error state with retry when the pet cannot load', async () => {
    (api.getPet as jest.Mock).mockRejectedValue(new ApiError(500, 'UNKNOWN_ERROR', ''));
    await renderWithProviders(<AttributesScreen />);
    expect(await screen.findByRole('button', { name: 'Tentar de novo' })).toBeOnTheScreen();
  });

  it('says there is nothing to spend when there are no unspent points', async () => {
    (api.getPet as jest.Mock).mockResolvedValue(makePet({ unspent_attribute_points: 0 }));
    await renderWithProviders(<AttributesScreen />);
    expect(await screen.findByTestId('no-points')).toBeOnTheScreen();
    expect(screen.getByLabelText('Aumentar Força')).toBeDisabled();
  });
});
