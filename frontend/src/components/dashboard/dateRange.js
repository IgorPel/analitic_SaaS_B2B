import apiClient from '../../api/axios';

export const DATE_RANGE_OPTIONS = [
  { value: 'latest_7_days', label: 'Останні 7 днів наявних даних' },
  { value: 'latest_30_days', label: 'Останні 30 днів наявних даних' },
  { value: 'latest_90_days', label: 'Останні 90 днів наявних даних' },
  { value: 'last_7_days', label: 'Останні 7 днів (від сьогодні)' },
  { value: 'last_30_days', label: 'Останні 30 днів (від сьогодні)' },
  { value: 'all_time', label: 'За весь час' },
  { value: 'custom', label: 'Свій період...' },
];

const RANGE_CACHE_TTL_MS = 60 * 1000;
const dataRangeCache = new Map();

export function toISODate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export function parseISODate(value) {
  if (!value) return null;
  const [y, m, d] = String(value).slice(0, 10).split('-').map(Number);
  if (!y || !m || !d) return null;
  const date = new Date(y, m - 1, d);
  return Number.isNaN(date.getTime()) ? null : date;
}

function shiftDays(date, days) {
  const copy = new Date(date);
  copy.setDate(copy.getDate() + days);
  return copy;
}

export function clearDataRangeCache() {
  dataRangeCache.clear();
}

export function fetchDataRange(stores = []) {
  const key = [...stores].sort().join(',');
  const cached = dataRangeCache.get(key);
  if (cached && Date.now() - cached.time < RANGE_CACHE_TTL_MS) {
    return cached.promise;
  }

  const params = new URLSearchParams();
  stores.forEach((id) => params.append('stores_id', id));

  const promise = apiClient
    .get('/data-range/', { params })
    .then((res) => res.data)
    .catch((err) => {
      dataRangeCache.delete(key);
      throw err;
    });

  dataRangeCache.set(key, { promise, time: Date.now() });
  return promise;
}

export async function resolveDateRange(para = {}, stores = []) {
  const range = para.date_range || 'last_30_days';

  if (range && typeof range === 'object') {
    return { start_date: range.start, end_date: range.end };
  }

  if (range === 'custom') {
    if (para.start_date && para.end_date) {
      return { start_date: para.start_date, end_date: para.end_date };
    }
    return null;
  }

  const match = /^(last|latest)_(\d+)_days$/.exec(range);

  if (match && match[1] === 'last') {
    const days = Number(match[2]);
    const end = new Date();
    return { start_date: toISODate(shiftDays(end, -(days - 1))), end_date: toISODate(end) };
  }

  const bounds = await fetchDataRange(stores);
  const maxDate = parseISODate(bounds?.max_date);
  const minDate = parseISODate(bounds?.min_date);
  if (!maxDate) return null;

  if (match && match[1] === 'latest') {
    const days = Number(match[2]);
    let start = shiftDays(maxDate, -(days - 1));
    if (minDate && start < minDate) start = minDate;
    return { start_date: toISODate(start), end_date: toISODate(maxDate) };
  }

  return { start_date: toISODate(minDate || maxDate), end_date: toISODate(maxDate) };
}

