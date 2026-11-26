import type { PetColor } from '@/api/types';

/**
 * Pet color choices (screen 24). This is pet content, not UI chrome, so it is kept apart
 * from the design tokens. Shown as the soft halo behind the PNG placeholder until the Rive
 * file can recolor the pet itself. The backend accepts any key; these are the ones the app offers.
 */
const DEFAULT_HALO = '#E6E4FB';

export const petHalo: Record<string, string> = {
  default: DEFAULT_HALO,
  lilac: '#E6E4FB',
  mint: '#DDF3EA',
  peach: '#FCE6DA',
  sky: '#DCEBFA',
};

export const DEFAULT_PET_COLOR: PetColor = 'default';

/** Halo for any color key the backend returns, with a neutral fallback for unknown keys. */
export const haloFor = (color: PetColor): string => petHalo[color] ?? DEFAULT_HALO;
