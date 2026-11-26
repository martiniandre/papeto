import type { ConsentRecord } from '@/api/types';

import { nextOnboardingRoute } from './nextRoute';
import { petNameSchema } from './schemas';

const consent = (type: ConsentRecord['type'], accepted = true): ConsentRecord => ({
  type,
  version: '1.0',
  accepted,
  recorded_at: '2026-11-25T10:00:00Z',
});

describe('nextOnboardingRoute', () => {
  it('asks for consents when any of the two is missing', () => {
    expect(nextOnboardingRoute({ consents: [] }, { name: 'Bolinha' })).toBe('/(onboarding)/age-terms');
    expect(
      nextOnboardingRoute({ consents: [consent('terms_privacy'), consent('meal_data', false)] }, { name: 'B' }),
    ).toBe('/(onboarding)/age-terms');
  });

  it('asks for the pet name next', () => {
    expect(
      nextOnboardingRoute({ consents: [consent('terms_privacy'), consent('meal_data')] }, { name: '' }),
    ).toBe('/(onboarding)/name-pet');
  });

  it('sends an onboarded account straight to Home', () => {
    expect(
      nextOnboardingRoute({ consents: [consent('terms_privacy'), consent('meal_data')] }, { name: 'Bolinha' }),
    ).toBe('/(tabs)/home');
  });
});

describe('petNameSchema', () => {
  it('requires a name of at most 20 characters', () => {
    expect(petNameSchema.safeParse({ name: '  ' }).success).toBe(false);
    expect(petNameSchema.safeParse({ name: 'a'.repeat(20) }).success).toBe(true);
    expect(petNameSchema.safeParse({ name: 'a'.repeat(21) }).success).toBe(false);
  });
});
