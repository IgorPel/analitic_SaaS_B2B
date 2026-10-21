import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  const hasToken = isAuthenticated || !!localStorage.getItem('access_token');

  if (!hasToken) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
