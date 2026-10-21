import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    company_name: '',
  });

  const [fieldErrors, setFieldErrors] = useState({});
  const [generalError, setGeneralError] = useState('');

  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    if (fieldErrors[name]) {
      setFieldErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFieldErrors({});
    setGeneralError('');

    try {
      await register(formData);
      console.log("WORK - 1")
      navigate('/');
    } catch (err) {

      if (err.response && err.response.data) {
        const data = err.response.data;

        if (typeof data === 'object' && !Array.isArray(data)) {
          setFieldErrors(data);
        } else {
          setGeneralError('Некоректні дані форми.');
        }
      }

      else {
        setGeneralError('Не вдалося з’єднатися із сервером. Спробуйте пізніше.');
      }
    }
  };

  return (
    <div style={{ maxWidth: '420px', margin: '4rem auto', padding: '2rem', background: '#fff', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
      <h2 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>Реєстрація компанії</h2>

      {generalError && (
        <div style={{ padding: '0.75rem', marginBottom: '1rem', background: '#fee2e2', color: '#dc2626', borderRadius: '4px', fontSize: '0.9rem' }}>
          {generalError}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>

        <div>
          <input
            type="text"
            name="company_name"
            placeholder="Назва компанії"
            value={formData.company_name}
            onChange={handleChange}
            required
            style={{
              width: '100%',
              padding: '0.75rem',
              borderRadius: '4px',
              border: `1px solid ${fieldErrors.company_name ? '#ef4444' : '#ccc'}`,
              boxSizing: 'border-box'
            }}
          />
          {fieldErrors.company_name && (
            <span style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '4px', display: 'block' }}>
              {fieldErrors.company_name[0]}
            </span>
          )}
        </div>

        <div>
          <input
            type="text"
            name="username"
            placeholder="Ім'я користувача (логін)"
            value={formData.username}
            onChange={handleChange}
            required
            style={{
              width: '100%',
              padding: '0.75rem',
              borderRadius: '4px',
              border: `1px solid ${fieldErrors.username ? '#ef4444' : '#ccc'}`,
              boxSizing: 'border-box'
            }}
          />
          {fieldErrors.username && (
            <span style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '4px', display: 'block' }}>
              {fieldErrors.username[0]}
            </span>
          )}
        </div>

        <div>
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            style={{
              width: '100%',
              padding: '0.75rem',
              borderRadius: '4px',
              border: `1px solid ${fieldErrors.email ? '#ef4444' : '#ccc'}`,
              boxSizing: 'border-box'
            }}
          />
          {fieldErrors.email && (
            <span style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '4px', display: 'block' }}>
              {fieldErrors.email[0]}
            </span>
          )}
        </div>

        <div>
          <input
            type="password"
            name="password"
            placeholder="Пароль (від 8 символів)"
            value={formData.password}
            onChange={handleChange}
            required
            style={{
              width: '100%',
              padding: '0.75rem',
              borderRadius: '4px',
              border: `1px solid ${fieldErrors.password ? '#ef4444' : '#ccc'}`,
              boxSizing: 'border-box'
            }}
          />
          {fieldErrors.password && (
            <span style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '4px', display: 'block' }}>
              {fieldErrors.password[0]}
            </span>
          )}
        </div>

        <button
          type="submit"
          style={{ padding: '0.75rem', background: '#10b981', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          Створити акаунт
        </button>
      </form>

      <p style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.9rem' }}>
        Вже маєте акаунт? <Link to="/login" style={{ color: '#4f46e5', textDecoration: 'none' }}>Увійти</Link>
      </p>
    </div>
  );
}
