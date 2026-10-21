import { useState, useEffect } from 'react';
import apiClient from '../../api/axios';
import BasicChart from './BasicChart';

const parseDateRange = (rangeType) => {
  let start = new Date(2026, 6, 1);
  let end = new Date(2026, 6, 8);

  if (rangeType && typeof rangeType === 'object') {
    start = new Date(rangeType.start);
    end = new Date(rangeType.end);
  } else if (rangeType === 'last_30_days') {
    start.setDate(end.getDate() - 30);
  } else if (rangeType === 'last_7_days') {
    start.setDate(end.getDate() - 7);
  }

  if (isNaN(start.getTime()) || isNaN(end.getTime())) {
    return {
      start_date: '2026-07-01',
      end_date: '2026-07-08',
    };
  }

  return {
    start_date: '2026-07-01',
    end_date: '2026-07-08',
  };
};

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

  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(Boolean(endpoint));
  const [error, setError] = useState(null);

  const isFullWidth = Boolean(widget.fullWidth);
  const effectiveHeight = widget.customHeight || baseHeight;

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const dateParams = parseDateRange(widget.para?.date_range);
        const params = new URLSearchParams();

        if (dateParams.start_date) params.append('start_date', dateParams.start_date);
        if (dateParams.end_date) params.append('end_date', dateParams.end_date);

        if (widget.stores && widget.stores.length > 0) {
          widget.stores.forEach((id) => {
            params.append('stores_id', id);
          });
        }

        if (widget.para && widget.para.group_and_limit) {
          params.append('group_and_limit', JSON.stringify(widget.para.group_and_limit));
        }

        if (widget.para && widget.para.fill_blank) {
          params.append('fill_blank', JSON.stringify(widget.para.fill_blank));
        }

        if (widget.para && widget.para.unique_dates) {
          params.append('unique_dates', JSON.stringify(widget.para.unique_dates));
        }

        if (widget.para && widget.para.graphs) {
          params.append('graphs', JSON.stringify(widget.para.graphs));
        }

        const response = await apiClient.get(endpoint, { params });
        setData(response.data.data || response.data || []);
      } catch (err) {
        console.error(err);
        setError('Помилка завантаження даних');
      } finally {
        setLoading(false);
      }
    };

    if (endpoint) {
      fetchData();
    }
  }, [widget, endpoint]);

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
