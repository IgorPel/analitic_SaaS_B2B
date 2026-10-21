import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BasicChart from './dashboard/BasicChart';
import { useMemo } from 'react';

const WIDGET_TEMPLATES = {
  revenue: {
    name: 'Динаміка виторгу',
    func: 'revenue',
    defaultChart: 'Line',
    x_axis: 'date',
    y_axis: 'revenue',
    cols: {
      date: { name: 'Дата', type: 'date', func: 'timedelta' },
      revenue: { name: 'Виторг', type: 'number', func: 'float' }
    },

    defaultPer: {
      revenue: {
        radius: [4, 4, 0, 0],
        barSize: 35,
        xAxisId: false,
        nameSuffix: 'Revenue',
        fillOpacity: 1
      }
    },
    defaultXAxidx: {
      revenue: { stroke: '#64748b', orientation: 'bottom' }
    }
  },
  top_products: {
    name: 'Найпродавніші товари',
    func: 'top_products',
    defaultChart: 'Table',
    x_axis: 'product__name',
    y_axis: 'quantity_sum',
    cols: {
      product__name: { name: 'Назва товару', type: 'string', func: 'string' },
      quantity_sum: { name: 'Загальна кількість', type: 'number', func: 'float' }
    },
    defaultPer: {
      quantity_sum: {
        radius: [4, 4, 0, 0],
        barSize: 35,
        xAxisId: false,
        nameSuffix: 'Qty',
        fillOpacity: 1
      }
    },
    defaultXAxidx: {
      quantity_sum: { stroke: '#64748b', orientation: 'bottom' }
    }
  },
  ltv: {
    name: 'Довічна цінність (LTV)',
    func: 'ltv',
    defaultChart: 'Line',
    x_axis: 'date',
    y_axis: 'revenue',
    multiple: true,
    cols: {
      date: { name: 'Дата', type: 'date', func: 'timedelta' },
      customer: { name: 'Клієнт', type: 'string', func: 'string' },
      revenue: { name: 'Виторг', type: 'number', func: 'float' },
      cm_revenue: { name: 'Накопичений виторг', type: 'number', func: 'float' }
    },

    defaultPer: {
      revenue: {
        radius: [4, 4, 0, 0],
        barSize: 35,
        xAxisId: true,
        nameSuffix: 'Revenue',
        fillOpacity: 1
      },
      cm_revenue: {
        radius: [4, 4, 0, 0],
        barSize: 35,
        xAxisId: true,
        nameSuffix: 'CM Revenue',
        fillOpacity: 0.25
      }
    },
    defaultXAxidx: {
      revenue: { stroke: '#64748b', orientation: 'bottom' },
      cm_revenue: {}
    }
  }
};

const TEMPLATE_DATA = {
  revenue: [
    { date: '2026-09-01', revenue: 100 },
    { date: '2026-09-02', revenue: 150 },
    { date: '2026-09-03', revenue: 50 },
    { date: '2026-09-04', revenue: 100 },
    { date: '2026-09-05', revenue: 200 },
    { date: '2026-09-06', revenue: 300 },
    { date: '2026-09-07', revenue: 500 },
    { date: '2026-09-08', revenue: 100 }
  ],
  ltv: [
    { date: '2026-09-01', revenue: 100, cm_revenue: 100, customer: 'test1@gmail.com' },
    { date: '2026-09-02', revenue: 50, cm_revenue: 150, customer: 'test1@gmail.com' },
    { date: '2026-09-03', revenue: 100, cm_revenue: 250, customer: 'test1@gmail.com' },
    { date: '2026-09-04', revenue: 75, cm_revenue: 325, customer: 'test1@gmail.com' },
    { date: '2026-09-05', revenue: 150, cm_revenue: 475, customer: 'test1@gmail.com' },
    { date: '2026-09-06', revenue: 75, cm_revenue: 550  , customer: 'test1@gmail.com' },
    { date: '2026-09-07', revenue: 150, cm_revenue: 700, customer: 'test1@gmail.com' },
    { date: '2026-09-08', revenue: 150, cm_revenue: 850, customer: 'test1@gmail.com' },
    { date: '2026-09-01', revenue: 50, cm_revenue: 50, customer: 'test2@gmail.com' },
    { date: '2026-09-03', revenue: 75, cm_revenue: 125, customer: 'test2@gmail.com' },
    { date: '2026-09-05', revenue: 25, cm_revenue: 150, customer: 'test2@gmail.com' },
    { date: '2026-09-07', revenue: 100, cm_revenue: 250, customer: 'test2@gmail.com' },
    { date: '2026-09-02', revenue: 150, cm_revenue: 150, customer: 'test3@gmail.com' },
    { date: '2026-09-04', revenue: 100, cm_revenue: 250, customer: 'test3@gmail.com' },
    { date: '2026-09-06', revenue: 300, cm_revenue: 550, customer: 'test3@gmail.com' },
    { date: '2026-09-08', revenue: 25, cm_revenue: 575, customer: 'test3@gmail.com' }
  ],
  top_categories: [
    { date: '2026-09-01', revenue: 100 },
    { date: '2026-09-02', revenue: 150 },
    { date: '2026-09-03', revenue: 50 },
    { date: '2026-09-04', revenue: 100 },
    { date: '2026-09-05', revenue: 200 },
    { date: '2026-09-06', revenue: 300 },
    { date: '2026-09-07', revenue: 500 },
    { date: '2026-09-08', revenue: 100 }
  ]
};

function CreateRightDataInput({ template, colKey, value, onChange }) {
  const col = template.cols[colKey];
  if (!col) return null;

  const inputStyle = { width: '100%', padding: '0.5rem', marginTop: '0.25rem', boxSizing: 'border-box' };

  if (col.type === 'number') {
    return (
      <input
        type="number"
        value={value ?? 0}
        onChange={(e) => onChange(colKey, Number(e.target.value))}
        style={inputStyle}
      />
    );
  } else if (col.type === 'string') {
    return (
      <input
        type="text"
        value={value ?? ''}
        onChange={(e) => onChange(colKey, e.target.value)}
        style={inputStyle}
      />
    );
  } else if (col.type === 'date') {
    return (
      <input
        type="date"
        value={value ?? ''}
        onChange={(e) => onChange(colKey, e.target.value)}
        style={inputStyle}
      />
    );
  }
  return null;
}

export default function WidgetBuilderPage({ onSaveWidget }) {
  const navigate = useNavigate();

  const [barPerConfig, setBarPerConfig] = useState(WIDGET_TEMPLATES['revenue'].defaultPer);
  const [barXAxidxConfig, setBarXAxidxConfig] = useState(WIDGET_TEMPLATES['revenue'].defaultXAxidx);

  const [metric, setMetric] = useState('revenue');
  const [chartType, setChartType] = useState(WIDGET_TEMPLATES['revenue'].defaultChart);
  const [dateRange, setDateRange] = useState('last_30_days');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');

  const [uniqueDates, setUniqueDates] = useState(false);
  const [xAxis, setXAxis] = useState(WIDGET_TEMPLATES['revenue'].x_axis);
  const [graphs, setGraphs] = useState('No');

  const [useGroupLimit, setUseGroupLimit] = useState(false);
  const [limit, setLimit] = useState(5);
  const [orderBy, setOrderBy] = useState('');

  const [groupConfig, setGroupConfig] = useState({});

  const [useFillBlank, setUseFillBlank] = useState(false);
  const [FillBlank_KEY, setFillBlank_KEY] = useState('');
  const [FillBlank_UNIQUES, setFillBlank_UNIQUES] = useState('');

  const [fillBlankMethod, setFillBlankMethod] = useState('AtoZ');
  const [fillBlankStart, setFillBlankStart] = useState('');
  const [fillBlankEnd, setFillBlankEnd] = useState('');
  const [deltaValue, setDeltaValue] = useState(1);

  const [toFillConfig, setToFillConfig] = useState({});

  const template = WIDGET_TEMPLATES[metric];
  const data = TEMPLATE_DATA[metric] || [];

  const syncedXAxidx = {};
  Object.keys(barPerConfig || {}).forEach((colKey, idx) => {

    if (barPerConfig[colKey]?.xAxisId) {
      syncedXAxidx[colKey] =
        barXAxidxConfig?.[colKey] ||
        (idx === 0 ? { stroke: '#64748b', orientation: 'bottom' } : { hide: true });
    }
  });
  const currentChartConfig =
    chartType === 'Bar'
      ? {
          per: barPerConfig,
          type: 'Bar',
          x_axis: {
            x_axis: xAxis,
            x_axidx: syncedXAxidx
          },
          y_axis: template.y_axis,
          ...(template.multiple && graphs !== 'No' && { multiple: true })
        }
      : {
          type: chartType,
          x_axis: xAxis,
          y_axis: template.y_axis,
          ...(template.multiple && graphs !== 'No' && { multiple: true })
        };

  const handleMetricChange = (e) => {
    const newMetric = e.target.value;
    const newTemplate = WIDGET_TEMPLATES[newMetric];

    setMetric(newMetric);
    setChartType(newTemplate.defaultChart);
    setXAxis(newTemplate.x_axis);
    setGraphs('No');

    setBarPerConfig(JSON.parse(JSON.stringify(newTemplate.defaultPer || {})));
    setBarXAxidxConfig(JSON.parse(JSON.stringify(newTemplate.defaultXAxidx || {})));

    setFillBlank_KEY('');
    setFillBlank_UNIQUES('');
    setToFillConfig({});
    setGroupConfig({});
    setOrderBy('');
    setUniqueDates(false);
  };

  const handleBarPerChange = (colKey, field, value) => {
    setBarPerConfig((prev) => ({
      ...prev,
      [colKey]: {
        ...prev[colKey],
        [field]: value
      }
    }));
  };

  const handleToggleBarCol = (colKey, enabled) => {
    setBarPerConfig((prev) => {
      const updated = { ...prev };
      if (!enabled) {
        delete updated[colKey];
      } else {

        updated[colKey] = template.defaultPer?.[colKey] || {
          radius: [4, 4, 0, 0],
          barSize: 35,
          xAxisId: true,
          nameSuffix: template.cols[colKey]?.name || colKey,
          fillOpacity: 1
        };
      }
      return updated;
    });
  };

  const handleGroupChange = (colKey, func) => {
    setGroupConfig((prev) => {
      const updated = { ...prev };
      if (func === 'None') {
        delete updated[colKey];
      } else {
        updated[colKey] = func;
      }
      return updated;
    });
  };

  const sortOptions = Object.entries(groupConfig).flatMap(([key, func]) => {
    const alias = func === 'F' ? key : `${key}_${func.toLowerCase()}`;
    const colName = template.cols[key]?.name || key;
    return [
      { value: `-${alias}`, label: `${colName} (Спадання / Найбільші)` },
      { value: alias, label: `${colName} (Зростання / Найменші)` }
    ];
  });

  const handleFillBlankKeyChange = (e) => {
    setFillBlank_KEY(e.target.value);
    setFillBlank_UNIQUES('');
    setToFillConfig({});
    setFillBlankStart('');
    setDeltaValue(1);
    setFillBlankEnd('');
  };

  const handleFillBlankUniquesChange = (e) => {
    setFillBlank_UNIQUES(e.target.value);
  };

  const handleFillStrategyChange = (key, strategy) => {
    setToFillConfig((prev) => ({
      ...prev,
      [key]: {
        ...prev[key],
        strategy: strategy
      }
    }));
  };

  const handleDefaultValueChange = (key, val) => {
    setToFillConfig((prev) => ({
      ...prev,
      [key]: {
        ...prev[key],
        defaultVal: val
      }
    }));
  };

  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);

    const to_fill = {};
    remainingCols.forEach((colKey) => {
      const colConf = toFillConfig[colKey] || {};
      const colType = template.cols[colKey]?.type;
      const strategy = colConf.strategy || 'DefaultValue';
      const defaultVal =
        colConf.defaultVal !== undefined
          ? colConf.defaultVal
          : colType === 'number'
          ? 0
          : '';

      to_fill[colKey] = [strategy, defaultVal];
    });

    const finalWidget = {
      id: crypto.randomUUID(),
      func: metric,
      chart: currentChartConfig,
      stores: ['6a2d045a-25ad-442a-afd6-347168c9c535'],
      para: {
        date_range: dateRange,
        ...(dateRange === 'custom' && { start_date: customStartDate, end_date: customEndDate }),
        ...(xAxis !== template.x_axis && { x_axis: xAxis }),
        ...(graphs !== 'No' && { graphs: graphs }),
        ...(uniqueDates && { unique_dates: true }),

        ...(useGroupLimit && Object.keys(groupConfig).length > 0 && {
          group_and_limit: {
            limit: Number(limit),
            group_by: groupConfig,
            order_by: orderBy ? [orderBy] : []
          }
        }),

        ...(useFillBlank && FillBlank_KEY && {
          fill_blank: {
            method: fillBlankMethod,
            key: FillBlank_KEY,
            uniques: FillBlank_UNIQUES,
            data_type: template.cols[FillBlank_KEY]?.type === 'date' ? 'date' : 'float',
            ...(fillBlankMethod === 'AtoZ' && fillBlankStart && fillBlankEnd && {
              start: fillBlankStart,
              end: fillBlankEnd
            }),
            to_fill: to_fill,
            delta: {
              per: template.cols[FillBlank_KEY]?.type === 'date' ? 'days' : FillBlank_KEY,
              func: template.cols[FillBlank_KEY]?.func,
              value: deltaValue
            }
          }
        })
      }
    };

    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');

      const response = await fetch('http://localhost:8000/api/dashboard-preferences/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` })
        },
        body: JSON.stringify(finalWidget)
      });

      if (!response.ok) {
        throw new Error(`Помилка збереження: ${response.status}`);
      }

      const result = await response.json();
      console.log('Збережено в dashboard_preferences:', result);

      if (onSaveWidget) onSaveWidget(finalWidget);
      navigate('/');
    } catch (error) {
      console.error('Не вдалося зберегти віджет:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const processedPreviewData = useMemo(() => {
    let result = JSON.parse(JSON.stringify(TEMPLATE_DATA[metric] || []));
    if (!result.length) return [];

    if (dateRange === 'custom' && customStartDate && customEndDate) {
      result = result.filter((row) => !row.date || (row.date >= customStartDate && row.date <= customEndDate));
    }

    if (uniqueDates) {
      const groupedByDate = {};
      result.forEach((row) => {
        const key = `${row.date}_${row.customer || ''}`;
        if (!groupedByDate[key]) {
          groupedByDate[key] = { ...row };
        } else {
          Object.keys(template.cols).forEach((colKey) => {
            if (template.cols[colKey].type === 'number') {
              groupedByDate[key][colKey] = (groupedByDate[key][colKey] || 0) + (row[colKey] || 0);
            }
          });
        }
      });
      result = Object.values(groupedByDate);
    }

    if (useGroupLimit && Object.keys(groupConfig).length > 0) {
      const fCols = Object.keys(groupConfig).filter((k) => groupConfig[k] === 'F');
      const aggCols = Object.keys(groupConfig).filter((k) => groupConfig[k] !== 'F');

      if (fCols.length > 0) {
        const mainGroupCol = fCols[0];
        const grouped = {};

        result.forEach((row) => {
          const groupVal = row[mainGroupCol];
          if (!grouped[groupVal]) {
            grouped[groupVal] = { [mainGroupCol]: groupVal };
            aggCols.forEach((col) => {
              grouped[groupVal][`${col}_${groupConfig[col].toLowerCase()}`] = 0;
            });
          }
          aggCols.forEach((col) => {
            const func = groupConfig[col];
            const alias = `${col}_${func.toLowerCase()}`;
            const val = Number(row[col] || 0);
            if (func === 'Sum' || func === 'Avg') grouped[groupVal][alias] += val;
            if (func === 'Count') grouped[groupVal][alias] += 1;
            if (func === 'Max') grouped[groupVal][alias] = Math.max(grouped[groupVal][alias], val);
            if (func === 'Min') grouped[groupVal][alias] = Math.min(grouped[groupVal][alias], val);
          });
        });

        let groupedList = Object.values(grouped);
        if (orderBy) {
          const isDesc = orderBy.startsWith('-');
          const sortKey = isDesc ? orderBy.slice(1) : orderBy;
          groupedList.sort((a, b) => (isDesc ? (b[sortKey] || 0) - (a[sortKey] || 0) : (a[sortKey] || 0) - (b[sortKey] || 0)));
        }
        if (limit > 0) groupedList = groupedList.slice(0, Number(limit));

        if (template.multiple && graphs !== 'No') {
          const topIds = new Set(groupedList.map((item) => item[mainGroupCol]));
          result = result.filter((row) => topIds.has(row[mainGroupCol]));
        } else {
          result = groupedList;
        }
      }
    }

    if (useFillBlank && FillBlank_KEY) {
      const colType = template.cols[FillBlank_KEY]?.type;
      const allKeys = result.map((r) => r[FillBlank_KEY]).filter(Boolean).sort();

      const effectiveStart = (fillBlankMethod === 'AtoZ' && fillBlankStart) ? fillBlankStart : allKeys[0];
      const effectiveEnd = (fillBlankMethod === 'AtoZ' && fillBlankEnd) ? fillBlankEnd : allKeys[allKeys.length - 1];

      const steps = [];
      if (colType === 'date' && effectiveStart && effectiveEnd) {
        let curr = new Date(effectiveStart);
        const end = new Date(effectiveEnd);
        const stepDays = Number(deltaValue) || 1;
        while (curr <= end) {
          steps.push(curr.toISOString().split('T')[0]);
          curr.setDate(curr.getDate() + stepDays);
        }
      } else if (colType === 'number' && effectiveStart !== undefined && effectiveEnd !== undefined) {
        let curr = Number(effectiveStart);
        const end = Number(effectiveEnd);
        const step = Number(deltaValue) || 1;
        while (curr <= end) {
          steps.push(curr);
          curr += step;
        }
      }

      if (steps.length > 0) {

        const remainingCols = Object.keys(template.cols).filter(
          (key) => key !== FillBlank_KEY && key !== FillBlank_UNIQUES
        );

        const fillSingleGroup = (groupRows, uniqueVal = null) => {
          const dataMap = new Map(groupRows.map((item) => [item[FillBlank_KEY], item]));
          const filled = [];
          let lastKnown = {};

          steps.forEach((stepVal) => {
            if (dataMap.has(stepVal)) {
              const row = dataMap.get(stepVal);
              lastKnown = { ...row };
              filled.push(row);
            } else {
              const newRow = { [FillBlank_KEY]: stepVal };
              if (FillBlank_UNIQUES && uniqueVal !== null) {
                newRow[FillBlank_UNIQUES] = uniqueVal;
              }
              remainingCols.forEach((colKey) => {
                const conf = toFillConfig[colKey] || {};
                const strat = conf.strategy || 'DefaultValue';
                const defVal = conf.defaultVal ?? (template.cols[colKey]?.type === 'number' ? 0 : '');

                if (strat === 'DefaultValueLeft') {
                  newRow[colKey] = lastKnown[colKey] !== undefined ? lastKnown[colKey] : defVal;
                } else {
                  newRow[colKey] = defVal;
                }
              });
              filled.push(newRow);
            }
          });
          return filled;
        };

        if (FillBlank_UNIQUES) {
          const uniqueGroups = [...new Set(result.map((r) => r[FillBlank_UNIQUES]))];
          let allFilled = [];
          uniqueGroups.forEach((uVal) => {
            const groupRows = result.filter((r) => r[FillBlank_UNIQUES] === uVal);
            allFilled = allFilled.concat(fillSingleGroup(groupRows, uVal));
          });
          result = allFilled;
        } else {
          result = fillSingleGroup(result);
        }
      }
    }

    if (template.multiple && graphs !== 'No') {
      const pivoted = {};
      result.forEach((row) => {
        const xVal = row[xAxis];
        const groupVal = row[graphs];
        if (!pivoted[xVal]) pivoted[xVal] = { [xAxis]: xVal };

        Object.keys(template.cols).forEach((colKey) => {
          if (colKey !== xAxis && colKey !== graphs && row[colKey] !== undefined) {
            pivoted[xVal][`${groupVal}/${colKey}`] = row[colKey];
          }
        });
      });

      result = Object.values(pivoted).sort((a, b) => (a[xAxis] > b[xAxis] ? 1 : -1));
    }

    return result;
  }, [
    metric, dateRange, customStartDate, customEndDate, uniqueDates,
    useGroupLimit, groupConfig, orderBy, limit,
    useFillBlank, FillBlank_KEY, FillBlank_UNIQUES, fillBlankMethod, fillBlankStart, fillBlankEnd, deltaValue, toFillConfig,
    xAxis, graphs
  ]);

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '2rem' }}>Конструктор графіків</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>

        <div
          style={{
            background: '#fff',
            padding: '1.5rem',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem'
          }}
        >
          <label>
            Метрика:
            <select
              value={metric}
              onChange={handleMetricChange}
              style={{ width: '100%', padding: '0.5rem', marginTop: '0.5rem' }}
            >
              {Object.entries(WIDGET_TEMPLATES).map(([key, temp]) => (
                <option key={key} value={key}>
                  {temp.name}
                </option>
              ))}
            </select>
          </label>

          <label>
            Тип графіка:
            <select
              value={chartType}
              onChange={(e) => setChartType(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', marginTop: '0.5rem' }}
            >
              {['Line', 'Bar', 'Pie', 'Table'].map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </label>

          {chartType === 'Bar' && (
            <div style={{ marginTop: '0.5rem', padding: '1rem', background: '#f8fafc', borderLeft: '4px solid #f59e0b', borderRadius: '4px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <strong style={{ fontSize: '0.9rem', color: '#475569' }}>Налаштування стовпчиків (per):</strong>

              {Object.entries(template.cols)
                .filter(([key, col]) => col.type === 'number')
                .map(([colKey, col]) => {
                  const isEnabled = Boolean(barPerConfig[colKey]);
                  const conf = barPerConfig[colKey] || {};

                  return (
                    <div key={colKey} style={{ padding: '0.75rem', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '4px', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={isEnabled}
                          onChange={(e) => handleToggleBarCol(colKey, e.target.checked)}
                        />
                        <b>{col.name} ({colKey})</b>
                      </label>

                      {isEnabled && (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: '0.25rem', fontSize: '0.8rem' }}>
                          <label>
                            Ширина (barSize):
                            <input
                              type="number"
                              value={conf.barSize ?? 35}
                              onChange={(e) => handleBarPerChange(colKey, 'barSize', Number(e.target.value))}
                              style={{ width: '100%', padding: '0.35rem', marginTop: '0.2rem', boxSizing: 'border-box' }}
                            />
                          </label>

                          <label>
                            Прозорість (0.1 - 1):
                            <input
                              type="number"
                              step="0.05"
                              min="0.05"
                              max="1"
                              value={conf.fillOpacity ?? 1}
                              onChange={(e) => handleBarPerChange(colKey, 'fillOpacity', Number(e.target.value))}
                              style={{ width: '100%', padding: '0.35rem', marginTop: '0.2rem', boxSizing: 'border-box' }}
                            />
                          </label>

                          <label>
                            Суфікс (nameSuffix):
                            <input
                              type="text"
                              value={conf.nameSuffix ?? ''}
                              onChange={(e) => handleBarPerChange(colKey, 'nameSuffix', e.target.value)}
                              style={{ width: '100%', padding: '0.35rem', marginTop: '0.2rem', boxSizing: 'border-box' }}
                            />
                          </label>

                          <label>
                            Радіус верхній (px):
                            <input
                              type="number"
                              value={conf.radius?.[0] ?? 4}
                              onChange={(e) => {
                                const r = Number(e.target.value);
                                handleBarPerChange(colKey, 'radius', [r, r, 0, 0]);
                              }}
                              style={{ width: '100%', padding: '0.35rem', marginTop: '0.2rem', boxSizing: 'border-box' }}
                            />
                          </label>

                          <label style={{ gridColumn: 'span 2', display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
                            <input
                              type="checkbox"
                              checked={Boolean(conf.xAxisId)}
                              onChange={(e) => handleBarPerChange(colKey, 'xAxisId', e.target.checked)}
                            />
                            Окрема вісь X (xAxisId: true — для накладання стовпчиків)
                          </label>
                        </div>
                      )}
                    </div>
                  );
                })}
            </div>
          )}

          <div style={{ marginTop: '1rem', padding: '1rem', background: '#f8fafc', borderLeft: '4px solid #8b5cf6', borderRadius: '4px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>

            <label>
              <strong style={{ fontSize: '0.9rem', color: '#475569' }}>Вісь X (Головний вимір):</strong>
              <select
                value={xAxis}
                onChange={(e) => setXAxis(e.target.value)}
                style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
              >
                {Object.entries(template.cols).map(([key, col]) => (
                  <option key={key} value={key}>
                    {col.name} ({key})
                  </option>
                ))}
              </select>
            </label>

            {(template.multiple && (chartType === 'Line' || chartType === 'Bar')) && (
              <label>
                <strong style={{ fontSize: '0.9rem', color: '#475569' }}>Деталізація (Окремі лінії / Graphs):</strong>
                <select
                  value={graphs}
                  onChange={(e) => setGraphs(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
                >
                  <option value="No">-- Без поділу (Єдина лінія) --</option>

                  {Object.entries(template.cols)
                    .filter(([key, col]) => col.type === 'string')
                    .map(([key, col]) => (
                      <option key={key} value={key}>
                        Розділити по: {col.name} ({key})
                      </option>
                    ))}
                </select>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.75rem', color: '#64748b' }}>
                  *Якщо обрати поділ, графік намалює окрему лінію для кожного елемента.
                </p>
              </label>
            )}
          </div>
          <label>
            Період:
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', marginTop: '0.5rem' }}
            >
              <option value="last_7_days">Останні 7 днів</option>
              <option value="last_30_days">Останні 30 днів</option>
              <option value="all_time">За весь час</option>
              <option value="custom">Свій період...</option>
            </select>
          </label>

          {dateRange === 'custom' && (
            <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
              <label style={{ flex: 1 }}>
                Початок:
                <input
                  type="date"
                  value={customStartDate}
                  onChange={(e) => setCustomStartDate(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    marginTop: '0.5rem',
                    boxSizing: 'border-box',
                    border: '1px solid #ccc',
                    borderRadius: '4px'
                  }}
                />
              </label>

              <label style={{ flex: 1 }}>
                Кінець:
                <input
                  type="date"
                  value={customEndDate}
                  onChange={(e) => setCustomEndDate(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    marginTop: '0.5rem',
                    boxSizing: 'border-box',
                    border: '1px solid #ccc',
                    borderRadius: '4px'
                  }}
                />
              </label>
            </div>
          )}

          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', marginTop: '1rem' }}>
            <input
              type="checkbox"
              checked={useGroupLimit}
              onChange={(e) => setUseGroupLimit(e.target.checked)}
              style={{ width: '1.2rem', height: '1.2rem', cursor: 'pointer' }}
            />
            <b>Застосувати групування та ліміти (Топ-X)</b>
          </label>

          {useGroupLimit && (
            <div style={{ marginLeft: '0.5rem', padding: '1rem', background: '#f8fafc', borderLeft: '4px solid #10b981', borderRadius: '4px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>

              <label>
                Ліміт (Топ-X):
                <input
                  type="number" min="1" max="100" value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', boxSizing: 'border-box' }}
                />
              </label>

              <div style={{ marginTop: '0.5rem' }}>
                <strong style={{ fontSize: '0.9rem', color: '#475569' }}>Налаштування колонок:</strong>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
                  {Object.entries(template.cols).map(([key, col]) => (
                    <div key={key} style={{ padding: '0.5rem', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '4px' }}>
                      <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
                        <span><b>{col.name}</b> ({key}):</span>
                        <select
                          value={groupConfig[key] || 'None'}
                          onChange={(e) => handleGroupChange(key, e.target.value)}
                          style={{ padding: '0.25rem', width: '55%' }}
                        >
                          <option value="None">-- Не використовувати --</option>
                          <option value="F">Основа групування (F)</option>
                          <option value="Sum">Сума (Sum)</option>
                          <option value="Avg">Середнє (Avg)</option>
                          <option value="Count">Кількість (Count)</option>
                          <option value="Max">Максимум (Max)</option>
                          <option value="Min">Мінімум (Min)</option>
                        </select>
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {sortOptions.length > 0 && (
                <label>
                  Сортування:
                  <select
                    value={orderBy}
                    onChange={(e) => setOrderBy(e.target.value)}
                    style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
                  >
                    <option value="">-- Оберіть поле --</option>
                    {sortOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </label>
              )}
            </div>
          )}

          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', marginTop: '1rem' }}>
            <input
              type="checkbox"
              checked={uniqueDates}
              onChange={(e) => setUniqueDates(e.target.checked)}
              style={{ width: '1.2rem', height: '1.2rem', cursor: 'pointer' }}
            />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <b>Об'єднувати денні покупки (unique_dates)</b>
              <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 'normal' }}>
                *Групує кілька транзакцій одного клієнта за день в одну крапку на графіку.
              </span>
            </div>
          </label>

          {/* ЧЕКБОКС FILL BLANKS */}
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', marginTop: '1rem' }}>
            <input
              type="checkbox"
              checked={useFillBlank}
              onChange={(e) => setUseFillBlank(e.target.checked)}
              style={{ width: '1.2rem', height: '1.2rem', cursor: 'pointer' }}
            />
            <b>Заповнювати пропущені дні (Fill Blanks)</b>
          </label>

          {useFillBlank && (
            <div
              style={{
                marginLeft: '0.5rem',
                padding: '1rem',
                background: '#f8fafc',
                borderLeft: '4px solid #3b82f6',
                borderRadius: '4px',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem'
              }}
            >
              <label>
                Ключ послідовності (наприклад, Дата):
                <select
                  value={FillBlank_KEY}
                  onChange={handleFillBlankKeyChange}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
                >
                  <option value="">-- Оберіть поле --</option>
                  {Object.entries(template.cols).map(([key, col]) => (
                    <option key={key} value={key}>
                      {col.name} ({key})
                    </option>
                  ))}
                </select>
              </label>

              {FillBlank_KEY && (
                <label>
                  Унікальний ідентифікатор групи:
                  <select
                    value={FillBlank_UNIQUES}
                    onChange={handleFillBlankUniquesChange}
                    style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
                  >
                    <option value="">-- Оберіть поле або залиште порожнім --</option>
                    {Object.entries(template.cols)
                      .filter(([key]) => key !== FillBlank_KEY)
                      .map(([key, col]) => (
                        <option key={key} value={key}>
                          {col.name} ({key})
                        </option>
                      ))}
                  </select>
                </label>
              )}

             {FillBlank_KEY && (
                <div style={{ marginTop: '0.5rem' }}>
                  <label>Метод генерації прогалин:
                    <select
                      value={fillBlankMethod}
                      onChange={(e) => setFillBlankMethod(e.target.value)}
                      style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
                    >
                      <option value="AtoZ">Від А до Я (Вказати межі)</option>
                      <option value="in_container">З існуючих даних (in_container)</option>
                    </select>
                  </label>
                </div>
              )}

              {/* Динамічні інпути меж ТІЛЬКИ для методу AtoZ */}
              {FillBlank_KEY && fillBlankMethod === 'AtoZ' && (
                <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', padding: '0.5rem', background: '#fff', borderRadius: '4px', border: '1px solid #e2e8f0' }}>

                  {template.cols[FillBlank_KEY]?.type === 'date' && (
                    <>
                      <label style={{ flex: 1 }}>Від:
                        <input type="date" value={fillBlankStart} onChange={(e) => setFillBlankStart(e.target.value)} style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', boxSizing: 'border-box' }} />
                      </label>
                      <label style={{ flex: 1 }}>До:
                        <input type="date" value={fillBlankEnd} onChange={(e) => setFillBlankEnd(e.target.value)} style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', boxSizing: 'border-box' }} />
                      </label>
                    </>
                  )}

                  {template.cols[FillBlank_KEY]?.type === 'number' && (
                    <>
                      <label style={{ flex: 1 }}>Від:
                        <input type="number" value={fillBlankStart} onChange={(e) => setFillBlankStart(Number(e.target.value))} style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', boxSizing: 'border-box' }} />
                      </label>
                      <label style={{ flex: 1 }}>До:
                        <input type="number" value={fillBlankEnd} onChange={(e) => setFillBlankEnd(Number(e.target.value))} style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', boxSizing: 'border-box' }} />
                      </label>
                    </>
                  )}

                  {template.cols[FillBlank_KEY]?.type === 'string' && (
                    <>
                      <label style={{ flex: 1 }}>Від:
                        <input type="text" value={fillBlankStart} onChange={(e) => setFillBlankStart(e.target.value)} style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', boxSizing: 'border-box' }} />
                      </label>
                      <label style={{ flex: 1 }}>До:
                        <input type="text" value={fillBlankEnd} onChange={(e) => setFillBlankEnd(e.target.value)} style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', boxSizing: 'border-box' }} />
                      </label>
                    </>
                  )}
                </div>
              )}

              {/* НАЛАШТУВАННЯ КРОКУ (DELTA) */}
              {FillBlank_KEY && (
                <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '4px' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 'bold', color: '#475569' }}>
                    Крок заповнення прогалин (Delta):
                  </label>
                  <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                    <label style={{ flex: 1 }}>
                      Значення:
                      <input
                        type="number"
                        min="1"
                        value={deltaValue}
                        onChange={(e) => setDeltaValue(Number(e.target.value))}
                        style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', boxSizing: 'border-box' }}
                      />
                    </label>
                  </div>
                </div>
              )}

              {FillBlank_KEY &&
                Object.entries(template.cols)
                  .filter(([key]) => key !== FillBlank_KEY && key !== FillBlank_UNIQUES)
                  .map(([key, col]) => {
                    const colConfig = toFillConfig[key] || {};
                    const selectedStrategy = colConfig.strategy || 'DefaultValue';
                    const defaultValue = colConfig.defaultVal;

                    return (
                      <div
                        key={key}
                        style={{
                          padding: '0.75rem',
                          background: '#ffffff',
                          border: '1px solid #e2e8f0',
                          borderRadius: '4px'
                        }}
                      >
                        <label>
                          Стратегія для <b>{col.name}</b>:
                          <select
                            value={selectedStrategy}
                            onChange={(e) => handleFillStrategyChange(key, e.target.value)}
                            style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
                          >
                            <option value="DefaultValue">Стандартне значення</option>
                            <option value="DefaultValueLeft">Минуле значення (Forward Fill)</option>
                            <option value="DefaultValueRight">Наступне значення (Backward Fill)</option>
                            <option value="DefaultValueAverage">Середнє значення</option>
                          </select>
                        </label>

                        <div style={{ marginTop: '0.5rem' }}>
                          <label style={{ fontSize: '0.85rem', color: '#475569' }}>
                            Значення за замовчуванням:
                          </label>
                          <CreateRightDataInput
                            template={template}
                            colKey={key}
                            value={defaultValue}
                            onChange={handleDefaultValueChange}
                          />
                        </div>
                      </div>
                    );
                  })}

              <p style={{ margin: 0, fontSize: '0.8rem', color: '#64748b' }}>
                *Ця функція гарантує, що графік не матиме розривів у періоди відсутності даних.
              </p>
            </div>
          )}

          <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
            <button
              type="button"
              onClick={() => navigate('/')}
              style={{
                flex: 1,
                padding: '0.75rem',
                background: '#e5e7eb',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Скасувати
            </button>
            <button
              type="button"
              onClick={handleSave}
              style={{
                flex: 1,
                padding: '0.75rem',
                background: '#10b981',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              Зберегти
            </button>
          </div>
        </div>

        {/* ПРАВА КОЛОНКА */}
        <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: '8px', border: '2px dashed #cbd5e1' }}>
          <h4 style={{ marginBottom: '1rem', color: '#64748b' }}>Попередній перегляд:</h4>
          <BasicChart
            data={processedPreviewData}
            chart={currentChartConfig}
          />
        </div>
      </div>
    </div>
  );
}
