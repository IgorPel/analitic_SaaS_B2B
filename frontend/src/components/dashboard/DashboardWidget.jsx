import { useQuery } from '@tanstack/react-query';
import apiClient from '../../api/axios';
import BasicChart from './BasicChart';
import { resolveDateRange } from './dateRange';

const formatPeriod = (range) => {
  if (!range) return null;
  const fmt = (iso) => iso.split('-').reverse().join('.');
  return range.start_date === range.end_date
    ? fmt(range.start_date)
    : `${fmt(range.start_date)} – ${fmt(range.end_date)}`;
};

const EMPTY_RESULT = { data: [], period: null };

async function fetchWidgetData(endpoint, para, stores, signal) {
  const range = await resolveDateRange(para, stores);
  if (!range) return EMPTY_RESULT;

  const params = new URLSearchParams();
  params.append('start_date', range.start_date);
  params.append('end_date', range.end_date);

  stores.forEach((id) => params.append('stores_id', id));

  if (para.group_and_limit) {
    params.append('group_and_limit', JSON.stringify(para.group_and_limit));
  }

  if (para.fill_blank) {
    const fillBlank = { ...para.fill_blank };
    if (fillBlank.method === 'AtoZ' && fillBlank.data_type === 'date') {
      fillBlank.start = range.start_date;
      fillBlank.end = range.end_date;
    }
    params.append('fill_blank', JSON.stringify(fillBlank));
  }

  if (para.unique_dates) {
    params.append('unique_dates', JSON.stringify(para.unique_dates));
  }

  if (para.graphs) {
    params.append('graphs', JSON.stringify(para.graphs));
  }

  const response = await apiClient.get(endpoint, { params, signal });
  return { data: response.data.data || response.data || [], period: range };
}

export default function DashboardWidget({
  widget,
  onDelete,
  baseHeight = 320,
  onUpdateLayout,
}) {
  let endpoint = '';
  let anal_func = 'Невідома функція';

  if (widget.func === 'revenue') {
    endpoint = '/revenue/';
    anal_func = 'Динаміка доходу';
  } else if (widget.func === 'ltv') {
    endpoint = '/ltv/';
    anal_func = 'Довічна цінність клієнта';
  } else if (widget.func === 'top_categories') {
    endpoint = '/top-categories/';
    anal_func = 'Найпродавніші категорії';
  } else if (widget.func === 'top_products') {
    endpoint = '/top-products/';
    anal_func = 'Найпродавніші товари';
  }

  const isFullWidth = Boolean(widget.fullWidth);
  const effectiveHeight = widget.customHeight || baseHeight;

  const para = widget.para || {};
  const stores = widget.stores || [];

  const { data: result = EMPTY_RESULT, isLoading: loading, isError } = useQuery({
    queryKey: ['analytics', widget.func, stores, para],
    queryFn: ({ signal }) => fetchWidgetData(endpoint, para, stores, signal),
    enabled: Boolean(endpoint),
  });

  const { data, period } = result;
  const error = isError ? 'Помилка завантаження даних' : null;

  const wrapperStyle = {
    gridColumn: isFullWidth ? '1 / -1' : 'span 1',
    minWidth: 0,
    transition: 'all 0.25s ease',
  };

  if (loading) {
    return (
      <div style={wrapperStyle}>
        <div
          style={{
            background: '#fff',
            padding: '2rem',
            borderRadius: '10px',
            border: '1px dashed #ccc',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: effectiveHeight + 60,
          }}
        >
          Завантаження віджета...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={wrapperStyle}>
        <div
          style={{
            background: '#fff',
            padding: '1.5rem',
            borderRadius: '10px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
            minHeight: effectiveHeight + 60,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxSizing: 'border-box',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0, color: '#374151', fontSize: '1.15rem' }}>{anal_func}</h3>
            {onDelete && (
              <button
                type="button"
                onClick={() => onDelete(widget.id)}
                title="Видалити віджет"
                aria-label="Видалити віджет"
                style={{
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#ef4444',
                  padding: '6px',
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'background-color 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#fee2e2';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                  <line x1="10" y1="11" x2="10" y2="17" />
                  <line x1="14" y1="11" x2="14" y2="17" />
                </svg>
              </button>
            )}
          </div>
          <div
            style={{
              background: '#fee2e2',
              color: '#dc2626',
              padding: '1.5rem',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flex: 1,
            }}
          >
            {error}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={wrapperStyle}>
      <BasicChart
        data={data}
        chart={widget.chart}
        func={anal_func}
        subtitle={formatPeriod(period)}
        chartHeight={effectiveHeight}
        isFullWidth={isFullWidth}
        onToggleFullWidth={
          onUpdateLayout
            ? () => onUpdateLayout(widget.id, { fullWidth: !isFullWidth })
            : undefined
        }
        onChangeHeight={
          onUpdateLayout
            ? (newHeight) => onUpdateLayout(widget.id, { customHeight: newHeight })
            : undefined
        }
        onDelete={onDelete ? () => onDelete(widget.id) : undefined}
      />
    </div>
  );
}
