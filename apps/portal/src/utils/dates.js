/** Date helpers working with 'YYYY-MM-DD' strings in the local time zone. */

export function todayISO() {
  return shiftDays(0);
}

export function shiftDays(days) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${month}-${day}`;
}

/** '2026-10-07' -> 'Oct 7, 2026' */
export function formatDate(iso, options = { month: 'short', day: 'numeric', year: 'numeric' }) {
  if (!iso) return '-';
  const [year, month, day] = iso.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString('en-US', options);
}
