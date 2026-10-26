import { parseSeriesKey, shortPer, metricLabel } from './seriesUtils';

function formatTooltipMetricName(metric, chartData) {
  if (chartData?.cols?.[metric]?.name) {
    return chartData.cols[metric].name;
  }
  const str = String(metric ?? '');
  if (str.toLowerCase().startsWith('cm_')) {
    return `CM_${str.slice(3)}`;
  }
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function Swatch({ color, opacity = 1, dash, kind }) {
  if (kind === 'line') {
    return (
      <svg width="18" height="8" style={{ flexShrink: 0 }}>
        <line
          x1="0"
          y1="4"
          x2="18"
          y2="4"
          stroke={color}
          strokeWidth="2.5"
          strokeDasharray={dash && dash !== '0' ? dash : undefined}
        />
      </svg>
    );
  }
  return (
    <span
      style={{
        width: 10,
        height: 10,
        borderRadius: 2,
        background: color,
        opacity,
        border: `1px solid ${color}`,
        boxSizing: 'border-box',
        flexShrink: 0,
      }}
    />
  );
}

export function GroupedLegend({ groups, chartData, kind = 'bar', extraControl = null }) {
  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '6px 12px',
        fontSize: '0.78rem',
        color: '#374151',
        paddingBottom: 8,
      }}
    >
      {extraControl ? <div style={{ display: 'flex', alignItems: 'center' }}>{extraControl}</div> : <div />}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'flex-end',
          gap: '6px 12px',
        }}
      >
        {groups.map((group) => {
          if (group.per === null) {
            return group.metrics.map((m) => (
              <span key={m.metric} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                <Swatch color={m.color || group.color} opacity={m.opacity} dash={m.dash} kind={kind} />
                {metricLabel(m.metric, chartData)}
              </span>
            ));
          }

          return (
            <span
              key={group.per}
              title={group.per}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '2px 8px',
                borderRadius: 999,
                background: '#f9fafb',
                border: '1px solid #f3f4f6',
              }}
            >
              <span style={{ fontWeight: 600, color: group.color }}>{shortPer(group.per)}</span>
              {group.metrics.map((m) => (
                <span key={m.metric} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: '#6b7280' }}>
                  <Swatch color={group.color} opacity={m.opacity} dash={m.dash} kind={kind} />
                  {metricLabel(m.metric, chartData)}
                </span>
              ))}
            </span>
          );
        })}
      </div>
    </div>
  );
}

export function GroupedTooltip({ active, payload, label, chartData, xAxisKey, valueSuffix = '' }) {
  if (!active || !payload || payload.length === 0) return null;

  const format = (v) => `${Number(v || 0).toLocaleString('uk-UA')}${valueSuffix}`;

  const resolvedLabel =
    (xAxisKey && payload[0]?.payload?.[xAxisKey] !== undefined
      ? payload[0].payload[xAxisKey]
      : label) ?? '';

  const groups = new Map();
  payload.forEach((item) => {
    const { per, metric } = parseSeriesKey(item.dataKey);
    const groupKey = per ?? '__flat__';
    if (!groups.has(groupKey)) {
      groups.set(groupKey, { per, color: item.color, metrics: [] });
    }
    groups.get(groupKey).metrics.push({ metric, value: item.value });
  });

  return (
    <div
      style={{
        background: 'rgba(255, 255, 255, 0.97)',
        border: '1px solid #e5e7eb',
        borderRadius: 8,
        padding: '8px 12px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        fontSize: '0.8rem',
        pointerEvents: 'none',
      }}
    >
      {resolvedLabel !== '' && (
        <div
          style={{
            fontWeight: 600,
            color: '#111827',
            marginBottom: 6,
            borderBottom: '1px solid #f3f4f6',
            paddingBottom: 4,
          }}
        >
          {resolvedLabel}
        </div>
      )}
      {Array.from(groups.values()).map((group) => {
        const inlineMetrics = group.metrics
          .map((m) => `${formatTooltipMetricName(m.metric, chartData)}: ${format(m.value)}`)
          .join('; ');

        return (
          <div
            key={group.per ?? '__flat__'}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              marginBottom: 3,
              whiteSpace: 'nowrap',
            }}
          >
            {group.per !== null && (
              <>
                <span
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: group.color,
                    flexShrink: 0,
                  }}
                />
                <span style={{ fontWeight: 600, color: '#1f2937' }}>
                  {shortPer(group.per)}:
                </span>
              </>
            )}
            <span style={{ color: '#374151', fontWeight: 500 }}>{inlineMetrics}</span>
          </div>
        );
      })}
    </div>
  );
}
