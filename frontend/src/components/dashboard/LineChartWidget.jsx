import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { useMemo } from 'react';
import { GroupedLegend, GroupedTooltip } from './GroupedLegend';
import { LINE_DASHES, buildPerColors, parseSeriesKey } from './seriesUtils';

export default function LineChartWidget({ data, chart_data }) {
  const xAxisKey = chart_data?.x_axis?.x_axis || chart_data?.x_axis;

  const { series, legendGroups } = useMemo(() => {
    if (!data || data.length === 0) return { series: [], legendGroups: [] };

    const keys = new Set();
    data.forEach((row) => {
      Object.keys(row).forEach((key) => {
        if (key !== xAxisKey) keys.add(key);
      });
    });

    const parsed = Array.from(keys).map((key) => ({ key, ...parseSeriesKey(key) }));
    const pers = [...new Set(parsed.filter((p) => p.per !== null).map((p) => p.per))];
    const metrics = [...new Set(parsed.map((p) => p.metric))];

    const perColors = buildPerColors(pers);
    const flatColors = buildPerColors(metrics);
    const dashFor = (metric) => LINE_DASHES[metrics.indexOf(metric) % LINE_DASHES.length];

    const seriesList = parsed.map((p) => ({
      key: p.key,
      color: p.per !== null ? perColors[p.per] : (chart_data?.colors?.[metrics.indexOf(p.metric)] || flatColors[p.metric]),
      dash: p.per !== null ? dashFor(p.metric) : '0',
    }));

    const groups = pers.length
      ? pers.map((per) => ({
          per,
          color: perColors[per],
          metrics: metrics
            .filter((m) => keys.has(`${per}/${m}`))
            .map((m) => ({ metric: m, dash: dashFor(m) })),
        }))
      : [
          {
            per: null,
            metrics: seriesList.map((s) => ({ metric: s.key, color: s.color, dash: '0' })),
          },
        ];

    return { series: seriesList, legendGroups: groups };
  }, [data, xAxisKey, chart_data]);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
        <XAxis dataKey={xAxisKey} tick={{ fontSize: 11 }} />
        <YAxis width={60} tick={{ fontSize: 11 }} />
        <Tooltip content={(props) => <GroupedTooltip {...props} chartData={chart_data} xAxisKey={xAxisKey} />} />
        <Legend
          verticalAlign="top"
          align="right"
          content={() => <GroupedLegend groups={legendGroups} chartData={chart_data} kind="line" />}
        />
        {series.map((s) => (
          <Line
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.key}
            stroke={s.color}
            strokeDasharray={s.dash !== '0' ? s.dash : undefined}
            strokeWidth={2.5}
            dot={{ r: 3 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
