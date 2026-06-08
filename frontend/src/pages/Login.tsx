import React from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import api from '../services/api';
import { Mail, Lock, Loader2, ArrowRight } from 'lucide-react';

export default function Login() {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [loading, setLoading] = React.useState(false);
  const [errorMsg, setErrorMsg] = React.useState('');
  const { login } = useAuthStore();
  const navigate = useNavigate();

  const onSubmit = async (data: any) => {
    setLoading(true);
    setErrorMsg('');
    try {
      // 1. Get tokens
      const tokenRes = await api.post('auth/token/', {
        email: data.email,
        password: data.password
      });
      const { access, refresh } = tokenRes.data;
      
      // Save tokens temporarily to fetch profile
      localStorage.setItem('accessToken', access);
      localStorage.setItem('refreshToken', refresh);

      // 2. Get profile
      const profileRes = await api.get('auth/profile/');
      
      // 3. Log in Zustand
      login(access, refresh, profileRes.data);
      navigate('/');
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || 'Invalid email or password. Please try again.');
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-[#070b13] items-center justify-center p-4">
      {/* Background gradients */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[20%] left-[25%] w-[400px] h-[400px] bg-indigo-500/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[20%] right-[25%] w-[400px] h-[400px] bg-violet-500/10 rounded-full blur-[120px]" />
      </div>

      <div className="relative w-full max-w-md bg-[#0a0e1a]/80 border border-slate-800/80 rounded-2xl p-8 backdrop-blur-md shadow-2xl">
        {/* Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center font-bold text-white text-xl shadow-lg shadow-indigo-500/20 mb-3">
            V
          </div>
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Welcome back</h1>
          <p className="text-xs text-slate-400">Sign in to manage client documents & check compliance</p>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-lg text-center font-medium">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Email */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5">Email address</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                <Mail className="w-4 h-4" />
              </span>
              <input
                type="email"
                {...register('email', { required: 'Email is required' })}
                placeholder="you@agency.com"
                className="w-full bg-slate-900/50 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none rounded-lg py-2.5 pl-10 pr-4 text-sm text-slate-100 placeholder-slate-500 transition-all"
              />
            </div>
            {errors.email && (
              <p className="text-rose-400 text-[10px] mt-1 font-semibold">
                {errors.email.message as string}
              </p>
            )}
          </div>

          {/* Password */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-semibold text-slate-400">Password</label>
              <Link to="/forgot" className="text-[10px] font-semibold text-indigo-400 hover:text-indigo-300">
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                <Lock className="w-4 h-4" />
              </span>
              <input
                type="password"
                {...register('password', { required: 'Password is required' })}
                placeholder="••••••••"
                className="w-full bg-slate-900/50 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none rounded-lg py-2.5 pl-10 pr-4 text-sm text-slate-100 placeholder-slate-500 transition-all"
              />
            </div>
            {errors.password && (
              <p className="text-rose-400 text-[10px] mt-1 font-semibold">
                {errors.password.message as string}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg py-2.5 px-4 font-semibold text-sm transition-all duration-150 flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-indigo-600/10 hover:shadow-indigo-600/20 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Signing in...
              </>
            ) : (
              <>
                Sign In
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-slate-800/60 text-center">
          <p className="text-xs text-slate-400">
            Don't have an account?{' '}
            <Link to="/register" className="font-semibold text-indigo-400 hover:text-indigo-300">
              Create an organization
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
