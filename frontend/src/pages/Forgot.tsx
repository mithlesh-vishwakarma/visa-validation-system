import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft, Loader2 } from 'lucide-react';

export default function Forgot() {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const onSubmit = (_data: any) => {
    setLoading(true);
    // Simulate API dispatch
    setTimeout(() => {
      setLoading(false);
      setSubmitted(true);
    }, 1200);
  };

  return (
    <div className="flex min-h-screen bg-[#070b13] items-center justify-center p-4">
      <div className="relative w-full max-w-md bg-[#0a0e1a]/80 border border-slate-800/80 rounded-2xl p-8 backdrop-blur-md shadow-2xl">
        <div className="flex flex-col items-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center font-bold text-white text-xl shadow-lg shadow-indigo-500/20 mb-3">
            V
          </div>
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Reset Password</h1>
          <p className="text-xs text-slate-400 text-center">Enter your email and we'll dispatch instructions to recover access</p>
        </div>

        {submitted ? (
          <div className="space-y-4">
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs rounded-lg text-center font-medium">
              If an account is registered to that email address, password reset instructions will arrive shortly.
            </div>
            <Link
              to="/login"
              className="w-full flex items-center justify-center gap-2 text-xs font-semibold text-slate-400 hover:text-slate-200"
            >
              <ArrowLeft className="w-4 h-4" />
              Return to Login
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">Email address</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                  <Mail className="w-4 h-4" />
                </span>
                <input
                  type="email"
                  {...register('email', { required: 'Email is required' })}
                  placeholder="name@agency.com"
                  className="w-full bg-slate-900/50 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none rounded-lg py-2.5 pl-10 pr-4 text-sm text-slate-100 placeholder-slate-500 transition-all"
                />
              </div>
              {errors.email && (
                <p className="text-rose-400 text-[10px] mt-1 font-semibold">
                  {errors.email.message as string}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg py-2.5 px-4 font-semibold text-sm transition-all duration-150 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Dispatching link...
                </>
              ) : (
                'Dispatch Reset Instructions'
              )}
            </button>

            <div className="text-center pt-2">
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Back to Sign In
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
