import type { Config } from 'tailwindcss';

import { colors, fonts, radii, spacing, typeScale } from './src/theme/tokens';

const px = (scale: Record<string, number>) =>
  Object.fromEntries(Object.entries(scale).map(([key, value]) => [key, `${value}px`]));

export default {
  content: ['./app/**/*.{ts,tsx}', './src/**/*.{ts,tsx}'],
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  presets: [require('nativewind/preset')],
  theme: {
    extend: {
      colors: {
        primary: colors.primary,
        background: colors.background,
        surface: colors.surface,
        'on-primary': colors.onPrimary,
        ink: colors.text,
        'ink-secondary': colors.textSecondary,
        'input-border': colors.inputBorder,
        'points-bg': colors.pointsBg,
        'points-text': colors.pointsText,
      },
      fontFamily: {
        body: [fonts.regular],
        semibold: [fonts.semibold],
        heading: [fonts.bold],
      },
      fontSize: px(typeScale),
      spacing: px(spacing),
      borderRadius: px(radii),
      minHeight: { touch: '44px' },
      minWidth: { touch: '44px' },
    },
  },
  plugins: [],
} satisfies Config;
