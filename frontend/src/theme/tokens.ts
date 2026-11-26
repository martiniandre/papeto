/**
 * Design tokens. Values come from frontend/AGENTS.md; do not add new hues here
 * without a design decision. `surface` and `onPrimary` are plain white.
 */
export const colors = {
  primary: '#4F46E5',
  background: '#F8F9FC',
  text: '#171B2E',
  textSecondary: '#5E6478',
  inputBorder: '#7D839A',
  pointsBg: '#FCEBC0',
  pointsText: '#4A3410',
  surface: '#FFFFFF',
  onPrimary: '#FFFFFF',
  /** Destructive actions (delete). White text on it is 6.5:1. */
  danger: '#B42318',
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

export const radii = {
  sm: 8,
  md: 12,
  lg: 16,
  pill: 999,
} as const;

export const fonts = {
  regular: 'Nunito_400Regular',
  semibold: 'Nunito_600SemiBold',
  bold: 'Nunito_800ExtraBold',
} as const;

export const typeScale = {
  caption: 12,
  body: 16,
  subtitle: 18,
  title: 24,
  display: 30,
} as const;

/** Minimum touch target, in points (AGENTS.md accessibility rules). */
export const minTouchTarget = 44;
