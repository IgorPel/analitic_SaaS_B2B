import { useState } from 'react';
import { Link } from 'react-router-dom';
import LineChartWidget from './LineChartWidget';
import PieChartWidget from './PieChartWidget';
import TableChartWidget from './TableChartWidget';
import BarChartWidget from './BarChartWidget';

export default function BasicChart({
  data,
  chart,
  func,
  onDelete,
  chartHeight = 320,
  isFullWidth = false,
  onToggleFullWidth,
  onChangeHeight,
}) {
  const IsEmpty = !data || data.length === 0;
  const [dragHeight, setDragHeight] = useState(null);
  const isDragging = dragHeight !== null;
  const currentHeight = dragHeight ?? chartHeight;

  const handleMouseDownResize = (e) => {
    e.preventDefault();
    const startY = e.clientY;
    const startHeight = currentHeight;
    setDragHeight(startHeight);

    const onMouseMove = (moveEvent) => {
      const deltaY = moveEvent.clientY - startY;
      const nextHeight = Math.max(200, Math.min(800, startHeight + deltaY));
      setDragHeight(nextHeight);
    };

    const onMouseUp = (upEvent) => {
      const deltaY = upEvent.clientY - startY;
      const finalHeight = Math.max(200, Math.min(800, startHeight + deltaY));
      setDragHeight(null);
      if (onChangeHeight) {
        onChangeHeight(finalHeight);
      }
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const renderChart = () => {
    switch (chart.type) {
      case 'Line':
        return <LineChartWidget data={data} chart_data={chart} />;
      case 'Pie':
        return <PieChartWidget data={data} chart_data={chart} />;
      case 'Table':
        return <TableChartWidget data={data} chart_data={chart} />;
      case 'Bar':
        return <BarChartWidget data={data} chart_data={chart} />;
      default:
        return <p style={{ textAlign: 'center', marginTop: '2rem' }}>Невідомий тип: {chart.type}</p>;
    }
  };

  const iconBtnStyle = {
    background: 'transparent',
    border: '1px solid transparent',
    cursor: 'pointer',
    color: '#9ca3af',
    padding: '5px',
    borderRadius: '6px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s',
  };

  return (
    <div
      style={{
        background: '#fff',
        padding: '1.25rem 1.5rem 0.75rem 1.5rem',
        borderRadius: '10px',
        boxShadow: isDragging
          ? '0 8px 20px rgba(79, 70, 229, 0.15)'
          : '0 2px 6px rgba(0,0,0,0.05)',
        border: isDragging ? '1px solid #6366f1' : '1px solid #f3f4f6',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        transition: isDragging ? 'none' : 'box-shadow 0.2s, border-color 0.2s',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '0.75rem',
          gap: '0.5rem',
          flexWrap: 'wrap',
        }}
      >
        <h3 style={{ margin: 0, color: '#374151', fontSize: '1.1rem', fontWeight: 600 }}>
          {func}
        </h3>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>

          {onChangeHeight && (
            <div
              style={{
                display: 'flex',
                background: '#f3f4f6',
                borderRadius: '6px',
                padding: '2px',
                marginRight: '4px',
              }}
              title="Висота віджета"
            >
              {[
                { label: 'S', h: 240 },
                { label: 'M', h: 340 },
                { label: 'L', h: 480 },
              ].map((preset) => {
                const isActive = Math.abs(currentHeight - preset.h) < 35;
                return (
                  <button
                    key={preset.label}
                    type="button"
                    onClick={() => onChangeHeight(preset.h)}
                    style={{
                      border: 'none',
                      background: isActive ? '#fff' : 'transparent',
                      color: isActive ? '#4f46e5' : '#6b7280',
                      fontWeight: isActive ? '600' : '500',
                      fontSize: '0.72rem',
                      padding: '2px 7px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      boxShadow: isActive ? '0 1px 2px rgba(0,0,0,0.08)' : 'none',
                      transition: 'all 0.15s',
                    }}
                  >
                    {preset.label}
                  </button>
                );
              })}
            </div>
          )}

          {onToggleFullWidth && (
            <button
              type="button"
              onClick={onToggleFullWidth}
              title={isFullWidth ? 'Згорнути у звичайну колонку' : 'Розгорнути на всю ширину'}
              aria-label="Змінити ширину віджета"
              style={{
                ...iconBtnStyle,
                color: isFullWidth ? '#4f46e5' : '#9ca3af',
                background: isFullWidth ? '#eef2ff' : 'transparent',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = '#4f46e5';
                e.currentTarget.style.backgroundColor = '#eef2ff';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = isFullWidth ? '#4f46e5' : '#9ca3af';
                e.currentTarget.style.backgroundColor = isFullWidth ? '#eef2ff' : 'transparent';
              }}
            >
              {isFullWidth ? (
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="4 14 10 14 10 20" />
                  <polyline points="20 10 14 10 14 4" />
                  <line x1="14" y1="10" x2="21" y2="3" />
                  <line x1="3" y1="21" x2="10" y2="14" />
                </svg>
              ) : (
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="15 3 21 3 21 9" />
                  <polyline points="9 21 3 21 3 15" />
                  <line x1="21" y1="3" x2="14" y2="10" />
                  <line x1="3" y1="21" x2="10" y2="14" />
                </svg>
              )}
            </button>
          )}

          {onDelete && (
            <button
              type="button"
              onClick={onDelete}
              title="Видалити віджет"
              aria-label="Видалити віджет"
              style={iconBtnStyle}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = '#ef4444';
                e.currentTarget.style.backgroundColor = '#fee2e2';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = '#9ca3af';
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              <svg
                width="17"
                height="17"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                <line x1="10" y1="11" x2="10" y2="17" />
                <line x1="14" y1="11" x2="14" y2="17" />
              </svg>
            </button>
          )}
        </div>
      </div>

      <div
        style={{
          width: '100%',
          height: currentHeight,
          position: 'relative',
          overflowY: chart.type === 'Table' ? 'auto' : 'hidden',
          overflowX: 'auto',
          transition: isDragging ? 'none' : 'height 0.2s ease',
        }}
      >
        {IsEmpty ? (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: '#9ca3af',
              border: '2px dashed #e5e7eb',
              borderRadius: '8px',
            }}
          >
            <p style={{ marginBottom: '0.5rem' }}>Немає даних для відображення</p>
            <Link to="/upload/sales" style={{ color: '#4f46e5', textDecoration: 'none', fontSize: '0.9rem' }}>
              Завантажити файл продажів ➔
            </Link>
          </div>
        ) : (
          renderChart()
        )}
      </div>

      {onChangeHeight && (
        <div
          onMouseDown={handleMouseDownResize}
          title="Потягніть, щоб змінити висоту графіка"
          style={{
            height: '12px',
            marginTop: '4px',
            cursor: 'ns-resize',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            userSelect: 'none',
          }}
        >
          <div
            style={{
              width: '36px',
              height: '4px',
              borderRadius: '2px',
              background: isDragging ? '#6366f1' : '#e5e7eb',
              transition: 'background 0.2s',
            }}
          />
        </div>
      )}
    </div>
  );
}
