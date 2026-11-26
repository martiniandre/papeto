import { act, render, screen } from '@testing-library/react-native';
import { AccessibilityInfo } from 'react-native';

import { MOODS } from '@/api/types';

import { Pet } from './Pet';
import { celebratingArt, moodArt } from './art';

function mockReduceMotion(enabled: boolean) {
  jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(enabled);
}

describe('<Pet />', () => {
  afterEach(() => {
    jest.useRealTimers();
  });

  beforeEach(() => {
    jest.restoreAllMocks();
    jest.spyOn(AccessibilityInfo, 'announceForAccessibility').mockImplementation(() => undefined);
  });

  it.each([
    ['happy', 'Bolinha, feliz'],
    ['tired', 'Bolinha, cansado'],
    ['sleepy', 'Bolinha, com sono'],
    ['fainted', 'Bolinha, desmaiado'],
    ['paused', 'Bolinha, descansando'],
  ] as const)('labels mood %s for screen readers', async (mood, label) => {
    mockReduceMotion(true);
    await render(<Pet mood={mood} name="Bolinha" />);
    expect(await screen.findByLabelText(label)).toBeOnTheScreen();
    expect(screen.getByRole('image')).toBeOnTheScreen();
  });

  it('maps every mood to its own placeholder art', async () => {
    mockReduceMotion(true);
    for (const mood of MOODS) {
      const { unmount } = await render(<Pet mood={mood} name="Bolinha" />);
      await act(async () => {});
      expect(screen.getByTestId(`pet-art-${mood}`).props.source).toBe(moodArt[mood]);
      await unmount();
    }
  });

  it('uses the sleeping art for paused', async () => {
    expect(moodArt.paused).toBe(require('../../../assets/pet/paused.png'));
    expect(moodArt.paused).not.toBe(moodArt.sleepy);
  });

  it('plays the celebration, announces the event and returns to the mood art when it ends', async () => {
    // Fake timers: the celebration lasts 2500 ms, so a real timer makes this test depend on machine speed.
    jest.useFakeTimers();
    mockReduceMotion(false);
    await render(<Pet mood="happy" events={['celebrate']} name="Pipoca" />);
    await act(async () => {});
    expect(screen.getByTestId('pet-art-celebrate').props.source).toBe(celebratingArt);
    expect(AccessibilityInfo.announceForAccessibility).toHaveBeenCalledWith('Pipoca ganhou uma vida!');

    await act(async () => {
      jest.advanceTimersByTime(2500);
    });
    expect(screen.queryByTestId('pet-art-celebrate')).toBeNull();
    expect(screen.getByTestId('pet-art-happy').props.source).toBe(moodArt.happy);
  });

  it('celebrates and announces a level_up', async () => {
    mockReduceMotion(false);
    await render(<Pet mood="happy" events={['level_up']} name="Pipoca" />);
    await act(async () => {});
    expect(screen.getByTestId('pet-art-celebrate').props.source).toBe(celebratingArt);
    expect(AccessibilityInfo.announceForAccessibility).toHaveBeenCalledWith('Pipoca subiu de nível!');
  });

  it('keeps a static mood image with reduce motion, but still announces events', async () => {
    mockReduceMotion(true);
    await render(<Pet mood="happy" events={['wake_up']} name="Pipoca" />);
    await act(async () => {});
    const image = screen.getByTestId('pet-art-happy');
    expect(image.props.source).toBe(moodArt.happy);
    expect(screen.queryByTestId('pet-art-celebrate')).toBeNull();
    expect(AccessibilityInfo.announceForAccessibility).toHaveBeenCalledWith('Pipoca acordou!');
  });
});
