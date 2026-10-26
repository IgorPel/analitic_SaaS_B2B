import React, { useMemo, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { GroupedLegend, GroupedTooltip } from './GroupedLegend';
import { buildPerColors } from './seriesUtils';

function CreateBar(preference, per = null, colorsMap = {}) {
  return Object.entries(preference.per).map(([metricKey, metricConfig]) => {
    const actualDataKey = per ? `${per}/${metricKey}` : metricKey;

    const hasAxis = metricConfig.xAxisId && Object.hasOwn(preference.x_axis.x_axidx, metricKey);

    const currentXAxisId = hasAxis ? metricKey : undefined;
    const currentStackId = Object.hasOwn(metricConfig, 'stackId') ? per : undefined;

    const barColor = per ? colorsMap[per] : (colorsMap[metricKey] || '#3b82f6');

    return (
      <Bar
        key={actualDataKey}
        dataKey={actualDataKey}
        name={actualDataKey}
        xAxisId={currentXAxisId}
        stackId={currentStackId}
        fill={barColor}
        fillOpacity={metricConfig.fillOpacity ?? 0.8}
        stroke={barColor}
        radius={metricConfig.radius ?? [4, 4, 0, 0]}
        maxBarSize={metricConfig.barSize || 40}
      />
    );
  });
}

export default function BarChartWidget({ data, chart_data }) {
  const xAxisKey = chart_data?.x_axis?.x_axis || chart_data?.x_axis;
  const [groupGap, setGroupGap] = useState(chart_data?.barCategoryGap ?? 28);

  const pers = useMemo(() => {
    if (!data || data.length === 0) return [];

    const set = new Set();
    data.forEach((row) => {
      Object.keys(row).forEach((key) => {
        if (key !== xAxisKey && key.includes('/')) {
          set.add(key.slice(0, key.lastIndexOf('/')));
        }
      });
    });

    return Array.from(set);
  }, [data, xAxisKey]);

  const colorsMap = useMemo(() => {
    if (pers.length !== 0) return buildPerColors(pers);
    const metrics = Object.keys(chart_data?.per || {});
    return buildPerColors(metrics);
  }, [pers, chart_data]);

  const legendGroups = useMemo(() => {
    const metricEntries = Object.entries(chart_data?.per || {});
    if (pers.length !== 0) {
      return pers.map((per) => ({
        per,
        color: colorsMap[per],
        metrics: metricEntries.map(([metric, cfg]) => ({
          metric,
          opacity: cfg.fillOpacity ?? 0.8,
        })),
      }));
    }
    return [
      {
        per: null,
        metrics: metricEntries.map(([metric, cfg]) => ({
          metric,
          color: colorsMap[metric],
          opacity: cfg.fillOpacity ?? 0.8,
        })),
      },
    ];
  }, [pers, colorsMap, chart_data]);

  const gapControl = (
    <label
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        fontSize: '0.74rem',
        color: '#6b7280',
        background: '#f9fafb',
        padding: '2px 8px',
        borderRadius: 6,
        border: '1px solid #f3f4f6',
      }}
      title="Регулювання відступу між групами стовпчиків"
    >
      <span>Відступ груп:</span>
      <input
        type="range"
        min="5"
        max="55"
        step="5"
        value={groupGap}
        onChange={(e) => setGroupGap(Number(e.target.value))}
        style={{ width: 65, accentColor: '#4f46e5', cursor: 'pointer' }}
      />
      <span style={{ minWidth: 28, fontWeight: 600, color: '#374151' }}>{groupGap}%</span>
    </label>
  );

  return (
    <div style={{ width: '100%', height: '100%', minHeight: 200 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
          barCategoryGap={`${groupGap}%`}
          barGap={2}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />

          {chart_data?.x_axis && Object.hasOwn(chart_data.x_axis, 'x_axidx') ? (
            Object.entries(chart_data.x_axis.x_axidx).map(([axisId, config], idx) => (
              <XAxis
                key={axisId}
                xAxisId={axisId}
                dataKey={xAxisKey}
                hide={idx > 0}
                tick={{ fontSize: 11 }}
                {...config}
              />
            ))
          ) : (
            <XAxis dataKey={xAxisKey} tick={{ fontSize: 11 }} />
          )}

          <YAxis
            width={60}
            tick={{ fontSize: 11 }}
            tickFormatter={(val) => `${(val / 1000).toLocaleString('uk-UA')}k ₴`}
          />

          <Tooltip
            cursor={{ fill: 'rgba(99, 102, 241, 0.06)' }}
            content={(props) => (
              <GroupedTooltip
                {...props}
                chartData={chart_data}
                xAxisKey={xAxisKey}
                valueSuffix=" ₴"
              />
            )}
          />
          <Legend
            verticalAlign="top"
            align="right"
            content={() => (
              <GroupedLegend
                groups={legendGroups}
                chartData={chart_data}
                kind="bar"
                extraControl={gapControl}
              />
            )}
          />

          {pers.length !== 0 ? (
            pers.map((per) => (
              <React.Fragment key={per}>
                {CreateBar(chart_data, per, colorsMap)}
              </React.Fragment>
            ))
          ) : (
            CreateBar(chart_data, null, colorsMap)
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
