import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';

import { AuthProvider, useAuth } from './context/AuthContext';

import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import TestChart from './components/WeatherChart';
import WidgetBuilderPage from './components/dashboard/WidgetBuilderPage';

function AppContent() {

  const { isAuthenticated, logout } = useAuth();

  return (
    <Router>
      <div id="root">

        <nav style={{
          padding: '1rem 2rem',
          background: '#fff',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', gap: '1.5rem' }}>
            <Link to="/" style={{ textDecoration: 'none', color: '#4f46e5', fontWeight: 'bold' }}>
              Дашборд
            </Link>

            {isAuthenticated && (
              <>
                <Link to="/upload/warehouse" style={{ textDecoration: 'none', color: '#374151' }}>
                  Завантажити Warehouse
                </Link>
                <Link to="/upload/sales" style={{ textDecoration: 'none', color: '#374151' }}>
                  Завантажити Sales
                </Link>
              </>
            )}
          </div>

          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>

            {isAuthenticated ? (
              <button
                onClick={logout}
                style={{
                  padding: '0.5rem 1rem', background: '#ef4444', color: '#fff',
                  border: 'none', borderRadius: '4px', cursor: 'pointer'
                }}>
                Вийти
              </button>
            ) : (
              <>
                <Link to="/login" style={{
                  padding: '0.5rem 1rem', textDecoration: 'none', color: '#374151',
                  border: '1px solid #d1d5db', borderRadius: '4px', fontWeight: '500'
                }}>
                  Увійти
                </Link>
                <Link to="/register" style={{
                  padding: '0.5rem 1rem', textDecoration: 'none', color: '#fff',
                  background: '#4f46e5', borderRadius: '4px', fontWeight: '500'
                }}>
                  Реєстрація
                </Link>
              </>
            )}
          </div>
        </nav>

        <div style={{ padding: '2rem', width: '100%', boxSizing: 'border-box', background: '#f9fafb', minHeight: '100vh' }}>
          <Routes>

            <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />
            <Route path="/register" element={isAuthenticated ? <Navigate to="/" replace /> : <RegisterPage />} />
            <Route path="/test-chart" element={<TestChart />} />

            <Route path="/" element={
              isAuthenticated ? <DashboardPage /> : <Navigate to="/login" replace />
            } />

            <Route path="/builder" element={
              isAuthenticated ? <WidgetBuilderPage /> : <Navigate to="/login" replace />
            } />

            <Route path="/upload/warehouse" element={
              isAuthenticated ? <UploadPage type="catalog" /> : <Navigate to="/login" replace />
            } />

            <Route path="/upload/sales" element={
              isAuthenticated ? <UploadPage type="sales" /> : <Navigate to="/login" replace />
            } />

            <Route path="*" element={
              <div style={{ textAlign: 'center', marginTop: '3rem' }}>
                <h2>Сторінку не знайдено (404)</h2>
                <Link to="/">Повернутися на головну</Link>
              </div>
            } />

          </Routes>
        </div>

      </div>
    </Router>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
