import { ABORTED, ApiError, NETWORK_ERROR } from '@/api/client';
import { isLimitReachedToday } from '@/stores/mealFlow';

import { classifyAnalysisFailure } from './analysisOutcome';

const err = (status: number, code: string) => new ApiError(status, code, '');

describe('classifyAnalysisFailure', () => {
  it.each([
    [err(422, 'NOT_FOOD'), { kind: 'error', reason: 'not_food' }],
    [err(422, 'PHOTO_NOT_READABLE'), { kind: 'error', reason: 'unreadable' }],
    [err(503, 'VISION_UNAVAILABLE'), { kind: 'error', reason: 'ai_error' }],
    [err(0, NETWORK_ERROR), { kind: 'error', reason: 'offline' }],
    [err(429, 'DAILY_LIMIT_REACHED'), { kind: 'dailyLimit' }],
    [err(403, 'MEAL_CONSENT_REQUIRED'), { kind: 'consentRequired' }],
    [err(0, ABORTED), { kind: 'cancelled' }],
    [new Error('x'), { kind: 'error', reason: 'ai_error' }],
  ])('maps %p', (error, expected) => {
    expect(classifyAnalysisFailure(error)).toEqual(expected);
  });
});

describe('isLimitReachedToday', () => {
  it('resets at local midnight', () => {
    const today = new Date(2026, 10, 25, 23, 59);
    const tomorrow = new Date(2026, 10, 26, 0, 1);
    expect(isLimitReachedToday('2026-11-25', today)).toBe(true);
    expect(isLimitReachedToday('2026-11-25', tomorrow)).toBe(false);
    expect(isLimitReachedToday(null, today)).toBe(false);
  });
});
