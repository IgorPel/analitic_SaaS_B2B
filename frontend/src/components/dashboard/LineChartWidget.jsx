import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { useMemo } from 'react';

export default function LineChartWidget({ data, chart_data }) {
  const isEmpty = !data || data.length === 0;

  const dataKeys = useMemo(() => {
    if (!data || data.length === 0) return [];

    const allKeys = new Set();

    data.forEach(dayRow => {
      Object.keys(dayRow).forEach(key => {

        if (key !== chart_data.x_axis) {
          allKeys.add(key);
        }
      });
    });

    return Array.from(allKeys);
  }, [data, chart_data]);

  console.log(dataKeys)

  return (
    <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey={chart_data.x_axis.x_axis} />
          <YAxis />
          <Tooltip />
          {dataKeys.map((key, index) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={chart_data.colors?.[index] || "#4f46e5"}
              name={key.includes('/') ? key.split('/')[0] : key}
              strokeWidth={3}
              dot={{ r: 4 }}
            />
          ))}
        </LineChart>

    </ResponsiveContainer>
  );
}
