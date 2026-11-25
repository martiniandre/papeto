import type { ImageSourcePropType } from 'react-native';

import type { Mood } from '@/api/types';

/**
 * PNG placeholders until the Rive file exists (ADR 010).
 * Source art (bundle/arte): happy=pet-happy, tired=pet-tired, sleepy=pet-sleepy,
 * fainted=pet-fainted, paused=pet-sleeping (closest art: curled up asleep with a nightcap),
 * celebrate/wake_up one-shot=pet-celebrating.
 */
export const moodArt: Record<Mood, ImageSourcePropType> = {
  happy: require('../../../assets/pet/happy.png'),
  tired: require('../../../assets/pet/tired.png'),
  sleepy: require('../../../assets/pet/sleepy.png'),
  fainted: require('../../../assets/pet/fainted.png'),
  paused: require('../../../assets/pet/paused.png'),
};

export const celebratingArt: ImageSourcePropType = require('../../../assets/pet/celebrating.png');

/** Neutral front view used before a mood exists (name and meet screens). */
export const frontArt: ImageSourcePropType = require('../../../assets/pet/front.png');
