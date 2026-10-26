export const LINE_DASHES = ['0', '6 4', '2 3', '10 4 2 4'];

export function parseSeriesKey(key) {
  const str = String(key ?? '');
  const idx = str.lastIndexOf('/');
  if (idx === -1) return { per: null, metric: str };
  return { per: str.slice(0, idx), metric: str.slice(idx + 1) };
}

export function shortPer(per) {
  if (per === null || per === undefined) return '';
  return String(per).split('@')[0];
}

export function metricLabel(metric, chartData) {
  return chartData?.cols?.[metric]?.name || metric;
}

export function buildPerColors(pers) {
  const map = {};
  const step = pers.length ? 360 / pers.length : 0;
  pers.forEach((per, idx) => {
    map[per] = `hsl(${Math.floor(idx * step)}, 70%, 50%)`;
  });
  return map;
}

