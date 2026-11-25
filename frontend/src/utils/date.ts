/** Local calendar day as YYYY-MM-DD, in the device timezone. Display/UI only, never game rules. */
export function localDayKey(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

/** Short time for meal cards, e.g. "12:30" or "12/03, 12:30". */
export function formatMealTime(iso: string, now = new Date()): string {
  const date = new Date(iso);
  const time = `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
  if (localDayKey(date) === localDayKey(now)) return time;
  const day = `${String(date.getDate()).padStart(2, '0')}/${String(date.getMonth() + 1).padStart(2, '0')}`;
  return `${day}, ${time}`;
}
