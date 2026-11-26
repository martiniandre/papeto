import { create } from 'zustand';

export interface NotificationSettings {
  mealReminder: boolean;
  sleepy: boolean;
  weekly: boolean;
  quietHours: boolean;
}

const DEFAULTS: NotificationSettings = {
  mealReminder: true,
  sleepy: true,
  weekly: false,
  quietHours: true,
};

interface SettingsState {
  settings: NotificationSettings;
  set: (patch: Partial<NotificationSettings>) => void;
}

/**
 * TODO(backend): notification settings are not in docs/api.md or the OpenAPI yet (another worker is adding
 * them). Until then they live in memory only. When the endpoint exists, replace the body of this hook with
 * a TanStack Query read plus a PATCH mutation; the screen already handles `isLoading`, `isError`, `isSaving`.
 */
const useSettingsStore = create<SettingsState>((set) => ({
  settings: DEFAULTS,
  set: (patch) => set((state) => ({ settings: { ...state.settings, ...patch } })),
}));

export interface UseNotificationSettings {
  settings: NotificationSettings;
  isLoading: boolean;
  isError: boolean;
  isSaving: boolean;
  update: (patch: Partial<NotificationSettings>) => void;
  retry: () => void;
}

export function useNotificationSettings(): UseNotificationSettings {
  const settings = useSettingsStore((state) => state.settings);
  const set = useSettingsStore((state) => state.set);
  return {
    settings,
    isLoading: false,
    isError: false,
    isSaving: false,
    update: set,
    retry: () => undefined,
  };
}

/** Whether any pet notification is on (shown as "Ligados" in Profile). */
export function useNotificationsSummary(): boolean {
  return useSettingsStore((s) => s.settings.mealReminder || s.settings.sleepy || s.settings.weekly);
}

/** Test helper. */
export const resetNotificationSettings = () => useSettingsStore.setState({ settings: DEFAULTS });
