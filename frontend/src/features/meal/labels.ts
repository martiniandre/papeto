import i18n from '@/i18n';

/** Translates the backend's fixed food-group vocabulary; unknown groups are shown as sent. */
export function foodGroupLabel(group: string): string {
  const key = `meal.foodGroups.${group}`;
  return i18n.exists(key) ? i18n.t(key as never) : group;
}
