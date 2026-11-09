import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/axios';
import { useAuth } from '../context/AuthContext';
import { clearDataRangeCache } from '../components/dashboard/dateRange';

const POLL_INTERVAL_MS = 2000;
const TERMINAL_STATUSES = ['SUCCESS', 'FAILURE'];

async function fetchTaskIssues(taskId) {
  try {
    const response = await apiClient.get('/task-issues/', {
      params: { tasks_id: taskId },
    });
    return Array.isArray(response.data) ? response.data : [];
  } catch (err) {
    console.error('Не вдалося завантажити лог помилок:', err);
    return [];
  }
}

export default function UploadPage({type}) {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const [file, setFile] = useState(null);
  const [store, setStore] = useState(null);
  const [taskId, setTaskId] = useState(null);

  const [status, setStatus] = useState('IDLE');
  const [uploadError, setUploadError] = useState('');
  const url = type === 'sales' ? '/upload-sales-data/' : '/upload-store-data/';

  const { data: profile } = useQuery({
    queryKey: ['userProfile'],
    queryFn: () => apiClient.get('/auth/me/').then((res) => res.data),
    enabled: !user?.stores,
  });

  const stores = user?.stores || profile?.stores || [];
  const currentStore = store ?? stores[0]?.name ?? '';

  const taskQuery = useQuery({
    queryKey: ['taskStatus', taskId],
    queryFn: async () => {
      const response = await apiClient.get(`/check-status/${taskId}/`);
      const taskData = response.data;

      if (taskData.status === 'SUCCESS') {
        const issues = await fetchTaskIssues(taskId);
        clearDataRangeCache();
        queryClient.invalidateQueries({ queryKey: ['analytics'] });
        return { ...taskData, issues };
      }
      return taskData;
    },
    enabled: Boolean(taskId) && status === 'PROCESSING',
    refetchInterval: (query) =>
      TERMINAL_STATUSES.includes(query.state.data?.status) ? false : POLL_INTERVAL_MS,
    refetchIntervalInBackground: true,
    staleTime: 0,
    gcTime: 0,
  });

  const taskStatus = taskQuery.data?.status;

  let effectiveStatus = status;
  if (status === 'PROCESSING') {
    if (taskStatus === 'SUCCESS') effectiveStatus = 'SUCCESS';
    else if (taskStatus === 'FAILURE') effectiveStatus = 'ERROR';
  }

  const progress =
    effectiveStatus === 'SUCCESS'
      ? 100
      : Math.min(15 + taskQuery.dataUpdateCount * 15, 90);

  const errorMessage =
    status === 'PROCESSING' && taskStatus === 'FAILURE'
      ? taskQuery.data?.result || 'Помилка обробки файлу на сервері'
      : uploadError;

  const issues = taskQuery.data?.issues || [];

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setTaskId(null);
      setStatus('IDLE');
      setUploadError('');
    }
  };

  const handleUpload = async () => {
    if (!file || !currentStore) return;

    setStatus('UPLOADING');
    setUploadError('');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('store_name', currentStore);

    try {

      const response = await apiClient.post(url, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.data.task_id) {
        setTaskId(response.data.task_id);
        setStatus('PROCESSING');
      }
    } catch (err) {
      console.error(err);
      setStatus('ERROR');
      setUploadError(
        err.response?.data?.file?.[0] ||
        err.response?.data?.store_id?.[0] ||
        'Помилка завантаження файлу'
      );
    }
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '600px', margin: '0 auto' }}>
      <h2>Завантаження даних продажів (CSV)</h2>

      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
          Магазин (Store):
        </label>
        <input
          type="text"
          list="store-options"
          placeholder="Введіть назву або оберіть зі списку"
          value={currentStore}
          onChange={(e) => setStore(e.target.value)}
          disabled={effectiveStatus === 'UPLOADING' || effectiveStatus === 'PROCESSING'}
          style={{
            width: '100%',
            padding: '0.6rem',
            boxSizing: 'border-box',
            borderRadius: '6px',
            border: '1px solid #ccc',
          }}
        />
        <datalist id="store-options">
          {stores.map((s) => (
            <option key={s.id} value={s.name}>
            </option>
          ))}
        </datalist>
      </div>

      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
          Оберіть CSV файл:
        </label>
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          disabled={effectiveStatus === 'UPLOADING' || effectiveStatus === 'PROCESSING'}
        />
      </div>

      <button
        onClick={handleUpload}
        disabled={!file || !currentStore || effectiveStatus === 'UPLOADING' || effectiveStatus === 'PROCESSING'}
        style={{
          padding: '0.6rem 1.2rem',
          cursor: 'pointer',
          background: '#4f46e5',
          color: '#fff',
          border: 'none',
          borderRadius: '6px',
          fontWeight: 'bold',
        }}
      >
        {effectiveStatus === 'UPLOADING' ? 'Відправка...' : 'Завантажити CSV'}
      </button>

      {effectiveStatus === 'PROCESSING' && (
        <div style={{ marginTop: '1.5rem' }}>
          <p>Обробка в базі даних Celery... {progress}%</p>
          <div style={{ width: '100%', background: '#eee', height: '20px', borderRadius: '4px' }}>
            <div
              style={{
                width: `${progress}%`,
                background: '#4caf50',
                height: '100%',
                borderRadius: '4px',
                transition: 'width 0.3s ease',
              }}
            />
          </div>
        </div>
      )}

      {effectiveStatus === 'SUCCESS' && (
        <div style={{ marginTop: '1.5rem' }}>
          <p style={{ color: 'green', fontWeight: 'bold', marginBottom: '1rem' }}>
            ✅ Файл успішно оброблено! Дані готові для аналітики.
          </p>

          {issues.length > 0 && (
            <div style={{ background: '#fffbeb', border: '1px solid #f59e0b', borderRadius: '8px', padding: '1.5rem' }}>
              <h4 style={{ color: '#b45309', marginTop: 0, marginBottom: '0.5rem', display: 'flex', alignItems: 'center' }}>
                ⚠️ Увага: Знайдено розбіжності ({issues.length})
              </h4>
              <p style={{ fontSize: '0.9rem', color: '#92400e', marginBottom: '1rem', marginTop: 0 }}>
                Деякі рядки були оброблені з попередженнями. Перевірте їх нижче:
              </p>

              <div style={{
                maxHeight: '250px',
                overflowY: 'auto',
                background: '#fff',
                border: '1px solid #fcd34d',
                borderRadius: '6px',
                padding: '0.5rem'
              }}>
                {issues.map((issue, idx) => (
                  <div key={idx} style={{
                    padding: '0.5rem',
                    borderBottom: idx !== issues.length - 1 ? '1px solid #fef3c7' : 'none',
                    fontSize: '0.85rem',
                    color: '#374151'
                  }}>
                    <span style={{ color: '#dc2626', fontWeight: 'bold', marginRight: '0.5rem' }}>
                      Рядок {issue.row_number}:
                    </span>
                    {issue.description}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {effectiveStatus === 'ERROR' && (
        <p style={{ color: 'red', marginTop: '1.5rem', fontWeight: 'bold' }}>
          ❌ {errorMessage}
        </p>
      )}
    </div>
  );
}
