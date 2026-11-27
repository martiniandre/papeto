import type { Me, Pet } from '@/api/types';

/** Version of the legal documents the user accepts on screen 2 (legal draft v1.0). */
export const CONSENT_VERSION = '1.0';

export type OnboardingRoute =
  | '/(onboarding)/age-terms'
  | '/(onboarding)/name-pet'
  | '/(tabs)/home';

export function hasRequiredConsents(me: Pick<Me, 'consents'>): boolean {
  const accepted = (type: string) => me.consents.some((c) => c.type === type && c.accepted);
  return accepted('terms_privacy') && accepted('meal_data');
}

/**
 * Where a signed-in user goes (flow 1): unconfirmed adult or missing consents → 2, unnamed pet → 43, otherwise Home.
 * An existing, fully onboarded account goes straight to Home.
 */
export function nextOnboardingRoute(
  me: Pick<Me, 'consents' | 'adult_confirmed'>,
  pet: Pick<Pet, 'name'>,
): OnboardingRoute {
  if (!me.adult_confirmed || !hasRequiredConsents(me)) return '/(onboarding)/age-terms';
  if (!pet.name) return '/(onboarding)/name-pet';
  return '/(tabs)/home';
}
