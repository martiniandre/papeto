import { ABORTED, isApiError, NETWORK_ERROR } from '@/api/client';

export type AnalysisErrorReason = 'not_food' | 'unreadable' | 'offline' | 'ai_error';
export const ANALYSIS_ERROR_REASONS: readonly AnalysisErrorReason[] = [
  'not_food',
  'unreadable',
  'offline',
  'ai_error',
];

export type AnalysisFailure =
  | { kind: 'cancelled' }
  | { kind: 'dailyLimit' }
  | { kind: 'consentRequired' }
  | { kind: 'error'; reason: AnalysisErrorReason };

/** Maps a POST /meals failure to the next screen (10 Analysis error, 11 Daily limit, or 2 consent). */
export function classifyAnalysisFailure(error: unknown): AnalysisFailure {
  if (!isApiError(error)) return { kind: 'error', reason: 'ai_error' };
  switch (error.code) {
    case ABORTED:
      return { kind: 'cancelled' };
    case 'DAILY_LIMIT_REACHED':
      return { kind: 'dailyLimit' };
    case 'MEAL_CONSENT_REQUIRED':
      return { kind: 'consentRequired' };
    case 'NOT_FOOD':
      return { kind: 'error', reason: 'not_food' };
    case 'PHOTO_NOT_READABLE':
      return { kind: 'error', reason: 'unreadable' };
    case NETWORK_ERROR:
      return { kind: 'error', reason: 'offline' };
    default:
      return { kind: 'error', reason: 'ai_error' };
  }
}

/** ASSUMPTION: confidence threshold for the "check the items" hint is not in docs (0..1 scale). */
export const LOW_CONFIDENCE = 0.6;
