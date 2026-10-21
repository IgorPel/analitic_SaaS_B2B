import { useState, useEffect } from 'react';
import apiClient from '../api/axios';
import { useAuth } from '../context/AuthContext';

export default function UploadPage({type}) {
  const { user } = useAuth();

  const [file, setFile] = useState(null);
  const [store, setStore] = useState('');
  const [taskId, setTaskId] = useState(null);

  const [status, setStatus] = useState('IDLE');
  const [progress, setProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const [stores, setStores] = useState([]);
  const [issues, setIssues] = useState([]);
  const url = type === 'sales' ? '/upload-sales-data/' : '/upload-store-data/';

  useEffect(() => {
    if (user?.stores) {
      setStores(user.stores);
      if (user.stores.length > 0 && !store) {
        setStore(user.stores[0].name);
      }
    } else {
      apiClient.get('/auth/me/')
        .then((res) => {
          const fetchedStores = res.data.stores || [];
          setStores(fetchedStores);
          if (fetchedStores.length > 0 && !store) {
            setStore(fetchedStores[0].name);
          }
        })
        .catch((err) => console.error("Помилка завантаження магазинів:", err));
    }
  }, [user]);

  useEffect(() => {
    if (!taskId || status !== 'PROCESSING') return;

    const interval = setInterval(async () => {
      try {
        const response = await apiClient.get(`/check-status/${taskId}/`);
        const taskData = response.data;

        if (taskData.status === 'SUCCESS') {
          setStatus('SUCCESS');
          setProgress(100);
          clearInterval(interval);

          try {

             const issuesResponse = await apiClient.get('/task-issues/', {
                 params: { tasks_id: taskId }
             });

             if (issuesResponse.data && issuesResponse.data.length > 0) {
                 setIssues(issuesResponse.data);
             }
          } catch (err) {
             console.error("Не вдалося завантажити лог помилок:", err);
          }

        } else if (taskData.status === 'FAILURE') {
          setStatus('ERROR');
          setErrorMessage(taskData.result || 'Помилка обробки файлу на сервері');
          clearInterval(interval);
        } else {

          setProgress((prev) => (prev < 90 ? prev + 15 : prev));
        }
      } catch (err) {
        console.error('Помилка перевірки статусу таски:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [taskId, status]);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatus('IDLE');
      setProgress(0);
      setErrorMessage('');
    }
  };

  const handleUpload = async () => {
    if (!file || !store) return;

    setStatus('UPLOADING');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('store_name', store);

    try {

      const response = await apiClient.post(url, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.data.task_id) {
        setTaskId(response.data.task_id);
        setStatus('PROCESSING');
        setProgress(15);
      }
    } catch (err) {
      console.error(err);
      setStatus('ERROR');
      setErrorMessage(
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
          value={store || ''}
          onChange={(e) => setStore(e.target.value)}
          disabled={status === 'UPLOADING' || status === 'PROCESSING'}
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
          disabled={status === 'UPLOADING' || status === 'PROCESSING'}
        />
      </div>

      <button
        onClick={handleUpload}
        disabled={!file || !store || status === 'UPLOADING' || status === 'PROCESSING'}
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
        {status === 'UPLOADING' ? 'Відправка...' : 'Завантажити CSV'}
      </button>

      {status === 'PROCESSING' && (
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

      {status === 'SUCCESS' && (
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

      {status === 'ERROR' && (
        <p style={{ color: 'red', marginTop: '1.5rem', fontWeight: 'bold' }}>
          ❌ {errorMessage}
        </p>
      )}
    </div>
  );
}
