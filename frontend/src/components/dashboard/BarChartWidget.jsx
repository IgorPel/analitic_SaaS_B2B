import React, { useMemo } from 'react';
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

function CreateBar(preference, per = null, colorsMap = {}) {
  return Object.entries(preference.per).map(([metricKey, metricConfig]) => {
    const actualDataKey = per ? `${per}/${metricKey}` : metricKey;
    const actualName = per ? `${per} / ${metricKey}` : metricKey;

    const hasAxis = metricConfig.xAxisId && Object.hasOwn(preference.x_axis.x_axidx, metricKey);

    const currentXAxisId = hasAxis ? metricKey : undefined;
    const currentStackId = Object.hasOwn(metricConfig, 'stackId') ? per : undefined;

    const barColor = per ? colorsMap[per] : (colorsMap[metricKey] || '#3b82f6');

    return (
      <Bar
        key={actualDataKey}
        dataKey={actualDataKey}
        name={actualName}
        xAxisId={currentXAxisId}
        stackId={currentStackId}
        fill={barColor}
        fillOpacity={metricConfig.fillOpacity ?? 0.8}
        stroke={barColor}
        radius={metricConfig.radius ?? [4, 4, 0, 0]}
        barSize={metricConfig.barSize}
      />
    );
  });
}

export default function BarChartWidget({ data, chart_data }) {
  console.log(data);
  console.log(chart_data);
  const colorsMap = {};
  const pers = useMemo(() => {
    if (!data || data.length === 0) return [];

    const set = new Set();
    const xAxisKey = chart_data?.x_axis?.x_axis || chart_data?.x_axis;

    data.forEach((row) => {
      Object.keys(row).forEach((key) => {
        if (key !== xAxisKey && key.includes('/')) {
          const [per] = key.split('/');
          set.add(per);
        }
      });
    });

    return Array.from(set);
  }, [data, chart_data]);

  if (pers.length !== 0) {
    const step = 360 / pers.length;
    pers.forEach((per, idx) => {
      const hue = Math.floor(idx * step);
      colorsMap[per] = `hsl(${hue}, 70%, 50%)`;
    });
  } else {
    if (data && data.length > 0) {
      const firstRow = data[0];
      const keys = Object.keys(firstRow);

      const step = 360 / keys.length;
      keys.forEach((key, idx) => {
        const hue = Math.floor(idx * step);
        colorsMap[key] = `hsl(${hue}, 70%, 50%)`;
      });
    }
  }

  return (
    <div style={{ width: '100%', height: '100%', minHeight: 220 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
          barCategoryGap="15%"
          barGap={3}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />

          {Object.hasOwn(chart_data.x_axis, 'x_axidx') ? (
            Object.entries(chart_data.x_axis.x_axidx).map(([axisId, config]) => (
              <XAxis
                key={axisId}
                xAxisId={axisId}
                dataKey={chart_data.x_axis.x_axis}
                {...config}
              />
            ))
          ) : null}

          <YAxis

            tickFormatter={(val) => `${(val / 1000).toLocaleString('uk-UA')}k ₴`}
          />

          <Tooltip
            formatter={(value, name) => [
              `${Number(value || 0).toLocaleString('uk-UA')} ₴`,
              name,
            ]}
          />
          <Legend
            verticalAlign="top"
            align="right"
            wrapperStyle={{ paddingBottom: 15 }}
            formatter={(val) => {
              const [user, metric] = val.split(' / ');
              const shortUser = user ? user.split('@')[0] : val;
              return metric ? `${shortUser} (${metric})` : shortUser;
            }}
          />

          {pers.length !== 0 ? (
            pers.map((user) => (
              <React.Fragment key={user}>
                {CreateBar(chart_data, user, colorsMap)}
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
