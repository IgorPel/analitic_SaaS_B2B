import { useState, useEffect } from 'react';
import apiClient from '../api/axios';
import { Link } from 'react-router-dom';
import DashboardWidget from '../components/dashboard/DashboardWidget';

const STORAGE_KEY = 'dashboard_scale_settings_v1';

export default function DashboardPage() {
  const [preferences, setPreferences] = useState([]);
  const [isPrefsLoaded, setIsPrefsLoaded] = useState(false);

  const [gridMode, setGridMode] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      return saved.gridMode || 'auto';
    } catch {
      return 'auto';
    }
  });

  const [zoom, setZoom] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      return saved.zoom || 100;
    } catch {
      return 100;
    }
  });

  const [baseHeight, setBaseHeight] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      return saved.baseHeight || 320;
    } catch {
      return 320;
    }
  });

  const [windowWidth, setWindowWidth] = useState(
    typeof window !== 'undefined' ? window.innerWidth : 1280
  );

  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ gridMode, zoom, baseHeight })
      );
    } catch (e) {
      console.error('Помилка збереження налаштувань масштабу:', e);
    }
  }, [gridMode, zoom, baseHeight]);

  useEffect(() => {
    const fetchPreferences = async () => {
      try {
        const response = await apiClient.get('/dashboard-preferences/');
        const data = response.data;

        if (Array.isArray(data)) {
          setPreferences(data);
        } else if (data && data.json_data && Array.isArray(data.json_data)) {
          setPreferences(data.json_data);
        } else {
          setPreferences([]);
        }
      } catch (error) {
        console.error('Помилка завантаження налаштувань:', error);
        setPreferences([]);
      } finally {
        setIsPrefsLoaded(true);
      }
    };

    fetchPreferences();
  }, []);

  const handleDeleteWidget = async (widgetId) => {
    if (!widgetId) return;

    const isConfirmed = window.confirm('Ви впевнені, що хочете видалити цей віджет?');
    if (!isConfirmed) return;

    try {
      await apiClient.delete(`/dashboard-preferences/${widgetId}/`);
      setPreferences((prev) => prev.filter((w) => String(w.id) !== String(widgetId)));
    } catch (error) {
      console.error('Помилка видалення віджета:', error);
      alert('Не вдалося видалити віджет. Спробуйте пізніше.');
    }
  };

  const handleUpdateWidgetLayout = async (widgetId, layoutChanges) => {
    const updatedList = preferences.map((w) =>
      String(w.id) === String(widgetId) ? { ...w, ...layoutChanges } : w
    );
    setPreferences(updatedList);

    try {
      await apiClient.patch('/dashboard-preferences/', updatedList);
    } catch (err) {
      console.error('Не вдалося зберегти розмір віджета на сервері:', err);
    }
  };

  const handleBaseHeightChange = (newHeight) => {
    setBaseHeight(newHeight);
    const hasCustomHeights = preferences.some((w) => w.customHeight);
    if (hasCustomHeights) {
      const cleaned = preferences.map((w) => {
        const copy = { ...w };
        delete copy.customHeight;
        return copy;
      });
      setPreferences(cleaned);
      apiClient.patch('/dashboard-preferences/', cleaned).catch(() => {});
    }
  };

  const getGridTemplateColumns = () => {
    const isMobile = windowWidth < 768;
    const isTablet = windowWidth < 1100;

    if (isMobile) {
      return 'minmax(0, 1fr)';
    }

    if (gridMode === '1') {
      return 'minmax(0, 1fr)';
    }
    if (gridMode === '2') {
      return 'repeat(2, minmax(0, 1fr))';
    }
    if (gridMode === '3') {
      return isTablet
        ? 'repeat(2, minmax(0, 1fr))'
        : 'repeat(3, minmax(0, 1fr))';
    }

    return 'repeat(auto-fit, minmax(min(100%, 440px), 1fr))';
  };

  if (!isPrefsLoaded) {
    return <p style={{ textAlign: 'center', marginTop: '3rem' }}>Завантаження конфігурації дашборду...</p>;
  }

  return (
    <div
      style={{
        padding: windowWidth < 640 ? '1rem' : '1.5rem 2rem',
        width: '100%',
        boxSizing: 'border-box',
        background: '#f9fafb',
        minHeight: '100vh',
      }}
    >

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          marginBottom: '1.75rem',
        }}
      >
        <h1 style={{ color: '#111827', margin: 0, fontSize: windowWidth < 640 ? '1.5rem' : '1.85rem' }}>
          Аналітика продажів
        </h1>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '0.75rem',
          }}
        >

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '0.75rem',
              background: '#fff',
              padding: '0.45rem 0.75rem',
              borderRadius: '10px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
              border: '1px solid #e5e7eb',
            }}
          >

            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ fontSize: '0.8rem', color: '#6b7280', marginRight: '4px', fontWeight: 500 }}>
                Сітка:
              </span>
              {[
                { id: 'auto', label: 'Авто', title: 'Автоматична адаптивна сітка' },
                { id: '1', label: '1 кол.', title: '1 колонка (на всю ширину)' },
                { id: '2', label: '2 кол.', title: '2 колонки' },
                { id: '3', label: '3 кол.', title: '3 колонки' },
              ].map((opt) => {
                const active = gridMode === opt.id;
                return (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setGridMode(opt.id)}
                    title={opt.title}
                    style={{
                      padding: '4px 9px',
                      fontSize: '0.8rem',
                      fontWeight: active ? 600 : 500,
                      borderRadius: '6px',
                      border: 'none',
                      cursor: 'pointer',
                      background: active ? '#4f46e5' : '#f3f4f6',
                      color: active ? '#fff' : '#374151',
                      transition: 'all 0.15s',
                    }}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>

            <div style={{ width: '1px', height: '20px', background: '#e5e7eb' }} />

            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ fontSize: '0.8rem', color: '#6b7280', marginRight: '4px', fontWeight: 500 }}>
                Висота:
              </span>
              {[
                { h: 240, label: 'Компакт' },
                { h: 320, label: 'Стандарт' },
                { h: 440, label: 'Велика' },
              ].map((item) => {
                const active = baseHeight === item.h;
                return (
                  <button
                    key={item.h}
                    type="button"
                    onClick={() => handleBaseHeightChange(item.h)}
                    style={{
                      padding: '4px 8px',
                      fontSize: '0.8rem',
                      fontWeight: active ? 600 : 500,
                      borderRadius: '6px',
                      border: 'none',
                      cursor: 'pointer',
                      background: active ? '#EEF2FF' : 'transparent',
                      color: active ? '#4f46e5' : '#4b5563',
                      transition: 'all 0.15s',
                    }}
                  >
                    {item.label}
                  </button>
                );
              })}
            </div>

            <div style={{ width: '1px', height: '20px', background: '#e5e7eb' }} />

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.8rem', color: '#6b7280', fontWeight: 500 }}>
                Масштаб:
              </span>
              <button
                type="button"
                onClick={() => setZoom((z) => Math.max(75, z - 5))}
                title="Зменшити масштаб"
                style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '6px',
                  border: '1px solid #d1d5db',
                  background: '#fff',
                  color: '#374151',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  lineHeight: 1,
                }}
              >
                −
              </button>

              <input
                type="range"
                min="75"
                max="150"
                step="5"
                value={zoom}
                onChange={(e) => setZoom(Number(e.target.value))}
                title={`Масштаб: ${zoom}%`}
                style={{
                  width: '85px',
                  accentColor: '#4f46e5',
                  cursor: 'pointer',
                }}
              />

              <button
                type="button"
                onClick={() => setZoom((z) => Math.min(150, z + 5))}
                title="Збільшити масштаб"
                style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '6px',
                  border: '1px solid #d1d5db',
                  background: '#fff',
                  color: '#374151',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  lineHeight: 1,
                }}
              >
                +
              </button>

              <button
                type="button"
                onClick={() => setZoom(100)}
                title="Натисніть, щоб скинути масштаб на 100%"
                style={{
                  padding: '3px 7px',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  borderRadius: '6px',
                  border: 'none',
                  background: zoom === 100 ? '#f3f4f6' : '#e0e7ff',
                  color: zoom === 100 ? '#4b5563' : '#4338ca',
                  cursor: 'pointer',
                  minWidth: '46px',
                }}
              >
                {zoom}%
              </button>
            </div>
          </div>

          <Link
            to="/builder"
            style={{
              padding: '0.65rem 1.25rem',
              background: '#10b981',
              color: '#fff',
              textDecoration: 'none',
              borderRadius: '8px',
              fontWeight: 'bold',
              boxShadow: '0 4px 6px rgba(16, 185, 129, 0.2)',
              transition: 'background 0.2s',
              whiteSpace: 'nowrap',
            }}
          >
            + Створити графік
          </Link>
        </div>
      </div>

      {preferences.length === 0 ? (
        <div
          style={{
            textAlign: 'center',
            padding: '4rem 2rem',
            background: '#fff',
            borderRadius: '12px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
            color: '#6b7280',
          }}
        >
          <p style={{ fontSize: '1.25rem', fontWeight: 600, color: '#374151', marginBottom: '0.5rem' }}>
            Немає активних віджетів
          </p>
          <p style={{ marginBottom: '1.5rem', fontSize: '0.95rem' }}>
            Створіть свій перший аналітичний віджет за допомогою конструктора графіків.
          </p>
          <Link
            to="/builder"
            style={{
              display: 'inline-block',
              padding: '0.75rem 1.5rem',
              background: '#10b981',
              color: '#fff',
              textDecoration: 'none',
              borderRadius: '8px',
              fontWeight: 'bold',
              boxShadow: '0 4px 6px rgba(16, 185, 129, 0.2)',
            }}
          >
            + Додати графік
          </Link>
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: getGridTemplateColumns(),
            gap: '1.5rem',
            zoom: `${zoom}%`,
            transition: 'grid-template-columns 0.25s ease',
          }}
        >
          {preferences.map((widget, index) => (
            <DashboardWidget
              key={widget.id || index}
              widget={widget}
              baseHeight={baseHeight}
              onDelete={handleDeleteWidget}
              onUpdateLayout={handleUpdateWidgetLayout}
            />
          ))}
        </div>
      )}
    </div>
  );
}
