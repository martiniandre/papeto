import { useMe, useUpdateMe } from '@/api/queries';
import type { NotificationPrefs, NotificationPrefsPatch } from '@/api/types';

export interface NotificationSettings {
  mealReminder: boolean;
  sleepy: boolean;
  weekly: boolean;
  /** True when start and end differ (`start == end` means no quiet hours). */
  quietHours: boolean;
  quietStart: string;
  quietEnd: string;
}

/** Quiet hours offered by the toggle (docs/api.md example). */
export const DEFAULT_QUIET = { start: '22:00', end: '08:00' } as const;
const NO_QUIET = '00:00';

export function toSettings(prefs: NotificationPrefs): NotificationSettings {
  return {
    mealReminder: prefs.meal_reminder,
    sleepy: prefs.sleepy_notice,
    weekly: prefs.weekly_summary,
    quietHours: prefs.quiet_hours_start !== prefs.quiet_hours_end,
    quietStart: prefs.quiet_hours_start,
    quietEnd: prefs.quiet_hours_end,
  };
}

function toPatch(change: Partial<NotificationSettings>): NotificationPrefsPatch {
  const patch: NotificationPrefsPatch = {};
  if (change.mealReminder !== undefined) patch.meal_reminder = change.mealReminder;
  if (change.sleepy !== undefined) patch.sleepy_notice = change.sleepy;
  if (change.weekly !== undefined) patch.weekly_summary = change.weekly;
  if (change.quietHours !== undefined) {
    patch.quiet_hours_start = change.quietHours ? DEFAULT_QUIET.start : NO_QUIET;
    patch.quiet_hours_end = change.quietHours ? DEFAULT_QUIET.end : NO_QUIET;
  }
  return patch;
}

/** Whether any pet notice is on (shown as "Ligados" in Profile). */
export const anyNoticeOn = (prefs: NotificationPrefs): boolean =>
  prefs.meal_reminder || prefs.sleepy_notice || prefs.weekly_summary;

export interface UseNotificationSettings {
  settings: NotificationSettings | null;
  isLoading: boolean;
  isError: boolean;
  isSaving: boolean;
  saveFailed: boolean;
  update: (change: Partial<NotificationSettings>) => void;
  retry: () => void;
}

/** Screen 27: reads `notifications` from GET /me and saves each change with PATCH /me. */
export function useNotificationSettings(): UseNotificationSettings {
  const me = useMe();
  const save = useUpdateMe();
  return {
    settings: me.data ? toSettings(me.data.notifications) : null,
    isLoading: me.isPending,
    isError: me.isError,
    isSaving: save.isPending,
    saveFailed: save.isError,
    update: (change) => save.mutate({ notifications: toPatch(change) }),
    retry: () => void me.refetch(),
  };
}
