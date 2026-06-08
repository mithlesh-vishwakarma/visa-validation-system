import { useEffect } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import api from '../services/api';
import Layout from './Layout';
import { Loader2 } from 'lucide-react';

export default function ProtectedRoute() {
  const { isAuthenticated, user, setUser, logout, isLoading, setLoading } = useAuthStore();

  useEffect(() => {
    const fetchProfile = async () => {
      if (isAuthenticated && !user) {
        setLoading(true);
        try {
          const response = await api.get('auth/profile/');
          setUser(response.data);
        } catch (error) {
          console.error("Failed to fetch profile", error);
          logout();
        } finally {
          setLoading(false);
        }
      } else {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [isAuthenticated, user, setUser, logout, setLoading]);

  if (isLoading) {
    return (
      <div className="flex flex-col h-screen w-screen bg-[#070b13] items-center justify-center text-slate-200">
        <Loader2 className="w-10 h-10 text-indigo-500 animate-spin mb-4" />
        <p className="text-sm font-semibold tracking-wide text-slate-400">Loading VisaFlow AI...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <Layout>
      <Outlet />
    </Layout>
  );
}
