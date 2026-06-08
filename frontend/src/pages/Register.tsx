import React from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { Building2, Mail, Lock, User, Loader2, ArrowRight } from 'lucide-react';

export default function Register() {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [loading, setLoading] = React.useState(false);
  const [errorMsg, setErrorMsg] = React.useState('');
  const [success, setSuccess] = React.useState(false);
  const navigate = useNavigate();

  const onSubmit = async (data: any) => {
    setLoading(true);
    setErrorMsg('');
    try {
      await api.post('auth/register/', {
        email: data.email,
        password: data.password,
        first_name: data.first_name,
        last_name: data.last_name,
        organization_name: data.organization_name
      });
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err: any) {
      console.error(err);
      const details = err.response?.data;
      if (details && typeof details === 'object') {
        const firstKey = Object.keys(details)[0];
        setErrorMsg(`${firstKey}: ${details[firstKey]}`);
      } else {
        setErrorMsg('Registration failed. Please check your details and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-[#070b13] items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[15%] left-[20%] w-[450px] h-[450px] bg-indigo-500/5 rounded-full blur-[130px]" />
        <div className="absolute bottom-[15%] right-[20%] w-[450px] h-[450px] bg-violet-500/5 rounded-full blur-[130px]" />
      </div>

      <div className="relative w-full max-w-lg bg-[#0a0e1a]/80 border border-slate-800/80 rounded-2xl p-8 backdrop-blur-md shadow-2xl">
        <div className="flex flex-col items-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center font-bold text-white text-xl shadow-lg shadow-indigo-500/20 mb-3">
            V
          </div>
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Create VisaFlow AI Account</h1>
          <p className="text-xs text-slate-400">Establish a new organization and begin compliance audits</p>
        </div>

        {success ? (
          <div className="p-6 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs rounded-lg text-center font-medium">
            Organization created successfully! Redirecting to login page...
          </div>
        ) : (
          <>
            {errorMsg && (
              <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-lg text-center font-medium">
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Agency Name */}
              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-slate-400 mb-1.5">Agency/Organization Name</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                    <Building2 className="w-4 h-4" />
                  </span>
                  <input
                    type="text"
                    {...register('organization_name', { required: 'Organization name is required' })}
                    placeholder="Global Visa Consultants Ltd"
                    className="w-full bg-slate-900/50 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none rounded-lg py-2.5 pl-10 pr-4 text-sm text-slate-100 placeholder-slate-500 transition-all"
                  />
                </div>
                {errors.organization_name && (
                  <p className="text-rose-400 text-[10px] mt-1 font-semibold">
                    {errors.organization_name.message as string}
                  </p>
                )}
              </div>

              {/* First Name */}
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5">First Name</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                    <User className="w-4 h-4" />
                  </span>
                  <input
                    type="text"
                    {...register('first_name', { required: 'First name is required' })}
                    placeholder="Jane"
                    className="w-full bg-slate-900/50 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none rounded-lg py-2.5 pl-10 pr-4 text-sm text-slate-100 placeholder-slate-500 transition-all"
                  />
                </div>
                {errors.first_name && (
                  <p className="text-rose-400 text-[10px] mt-1 font-semibold">
                    {errors.first_name.message as string}
                  </p>
                )}
              </div>

              {/* Last Name */}
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5">Last Name</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                    <User className="w-4 h-4" />
                  </span>
                  <input
                    type="text"
                    {...register('last_name', { required: 'Last name is required' })}
                    placeholder="Doe"
                    className="w-full bg-slate-900/50 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none rounded-lg py-2.5 pl-10 pr-4 text-sm text-slate-100 placeholder-slate-500 transition-all"
                  />
                </div>
                {errors.last_name && (
                  <p className="text-rose-400 text-[10px] mt-1 font-semibold">
                    {errors.last_name.message as string}
                  </p>
                )}
              </div>

              {/* Email */}
              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-slate-400 mb-1.5">Work Email Address</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                    <Mail className="w-4 h-4" />
                  </span>
                  <input
                    type="email"
                    {...register('email', { required: 'Email is required' })}
                    placeholder="jane@company.com"
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
              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-slate-400 mb-1.5">Choose Password</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                    <Lock className="w-4 h-4" />
                  </span>
                  <input
                    type="password"
                    {...register('password', { required: 'Password is required', minLength: { value: 6, message: 'Min length is 6' } })}
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

              <div className="md:col-span-2 mt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg py-2.5 px-4 font-semibold text-sm transition-all duration-150 flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-indigo-600/10 hover:shadow-indigo-600/20 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Creating account...
                    </>
                  ) : (
                    <>
                      Get Started
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </form>
          </>
        )}

        <div className="mt-6 pt-6 border-t border-slate-800/60 text-center">
          <p className="text-xs text-slate-400">
            Already have an organization?{' '}
            <Link to="/login" className="font-semibold text-indigo-400 hover:text-indigo-300">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
