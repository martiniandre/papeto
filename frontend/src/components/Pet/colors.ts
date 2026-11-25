import type { PetColor } from '@/api/types';

/**
 * Pet color choices (screen 24). This is pet content, not UI chrome, so it is kept apart
 * from the design tokens. Shown as the soft halo behind the PNG placeholder until the Rive
 * file can recolor the pet itself. ASSUMPTION: the palette is not defined in the docs.
 */
export const petHalo: Record<PetColor, string> = {
  lilac: '#E6E4FB',
  mint: '#DDF3EA',
  peach: '#FCE6DA',
  sky: '#DCEBFA',
};

export const DEFAULT_PET_COLOR: PetColor = 'lilac';
