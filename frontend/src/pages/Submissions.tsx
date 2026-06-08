import React, { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import type { Submission, Client } from '../types';
import { 
  Plus, 
  Calendar, 
  ChevronRight, 
  Loader2, 
  Globe, 
  Award,
  Search
} from 'lucide-react';

export default function Submissions() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();
  const [modalOpen, setModalOpen] = React.useState(false);
  const [search, setSearch] = React.useState('');
  const [mutationError, setMutationError] = React.useState('');

  const { register, handleSubmit, setValue, reset, formState: { errors } } = useForm();

  // Fetch Submissions
  const { data: submissions = [], isLoading, error } = useQuery<Submission[]>({
    queryKey: ['submissions'],
    queryFn: async () => {
      const response = await api.get('submissions/');
      return response.data;
    }
  });

  // Fetch Clients for dropdown
  const { data: clients = [] } = useQuery<Client[]>({
    queryKey: ['clients'],
    queryFn: async () => {
      const response = await api.get('clients/');
      return response.data;
    }
  });

  // Create Submission Mutation
  const createSubmissionMutation = useMutation({
    mutationFn: async (newSub: any) => {
      const response = await api.post('submissions/', newSub);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
      setModalOpen(false);
      reset();
      navigate(`/submissions/${data.id}`);
    },
    onError: (err: any) => {
      setMutationError(err.response?.data?.detail || 'Failed to create application. Try again.');
    }
  });

  // Intercept state from client page
  useEffect(() => {
    if (location.state && (location.state as any).createForClient) {
      const client = (location.state as any).createForClient;
      setValue('client', client.id);
      setValue('country', client.country);
      setValue('visa_type', client.visa_type);
      setModalOpen(true);
      // Clear state so modal doesn't re-open
      window.history.replaceState({}, document.title);
    }
  }, [location.state, setValue]);

  const onSubmit = (data: any) => {
    setMutationError('');
    createSubmissionMutation.mutate(data);
  };

  const filteredSubmissions = submissions.filter(sub => 
    sub.client_detail.name.toLowerCase().includes(search.toLowerCase()) ||
    sub.country.toLowerCase().includes(search.toLowerCase()) ||
    sub.status.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Visa Applications</h1>
          <p className="text-xs text-slate-400">Initialize submissions and run automated rules checking on compliance files.</p>
        </div>
        <button
          onClick={() => { setMutationError(''); setModalOpen(true); }}
          className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg py-2.5 px-4 font-semibold text-xs transition-all duration-150 flex items-center gap-1.5 cursor-pointer shadow-lg shadow-indigo-600/10 hover:shadow-indigo-600/20"
        >
          <Plus className="w-4 h-4" />
          New Application
        </button>
      </div>

      {/* Search Filter */}
      <div className="flex items-center bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl px-3.5 py-2">
        <Search className="w-4 h-4 text-slate-500 mr-2.5" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search submissions by client name, destination country, status..."
          className="bg-transparent border-0 focus:outline-none w-full text-xs text-slate-100 placeholder-slate-500"
        />
      </div>

      {isLoading ? (
        <div className="flex h-[40vh] items-center justify-center text-slate-400">
          <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mr-3" />
          <span>Loading applications list...</span>
        </div>
      ) : error ? (
        <div className="p-6 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm rounded-xl text-center">
          Failed to fetch visa applications. Check backend connection.
        </div>
      ) : filteredSubmissions.length === 0 ? (
        <div className="p-12 bg-[#0a0e1a]/40 border border-slate-800/50 rounded-xl text-center">
          <p className="text-sm font-semibold text-slate-400">No active applications</p>
          <p className="text-xs text-slate-500 mt-1">Start by adding a client or initialize a new visa application.</p>
        </div>
      ) : (
        /* Submissions list */
        <div className="bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-[10px] font-bold text-slate-400 uppercase tracking-wider bg-slate-900/30">
                  <th className="py-3.5 px-4">Client Details</th>
                  <th className="py-3.5 px-4">Destination</th>
                  <th className="py-3.5 px-4">Visa Type</th>
                  <th className="py-3.5 px-4">Submission Date</th>
                  <th className="py-3.5 px-4">Compliance Status</th>
                  <th className="py-3.5 px-4">Score</th>
                  <th className="py-3.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 text-xs text-slate-300">
                {filteredSubmissions.map((sub) => (
                  <tr key={sub.id} className="hover:bg-slate-800/20 transition-all duration-100">
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center font-bold text-indigo-400">
                          {sub.client_detail.name[0].toUpperCase()}
                        </div>
                        <div>
                          <div className="font-semibold text-slate-200">{sub.client_detail.name}</div>
                          <div className="text-[10px] text-slate-500">{sub.client_detail.passport_number}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-200">
                      <div className="flex items-center gap-1.5">
                        <Globe className="w-3.5 h-3.5 text-indigo-400/80" />
                        {sub.country}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">{sub.visa_type}</td>
                    <td className="py-3.5 px-4 text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 text-slate-500" />
                        {new Date(sub.created_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded text-[8px] font-bold border ${
                        sub.status === 'Approved' ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-400' :
                        sub.status === 'Rejected' ? 'bg-rose-500/5 border-rose-500/20 text-rose-400' :
                        sub.status === 'Pending' ? 'bg-amber-500/5 border-amber-500/20 text-amber-400' :
                        'bg-indigo-500/5 border-indigo-500/20 text-indigo-400'
                      }`}>
                        {sub.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-bold">
                      {sub.validation_report ? (
                        <div className="flex items-center gap-1">
                          <Award className={`w-3.5 h-3.5 ${
                            sub.validation_report.status === 'Passed' ? 'text-emerald-400' :
                            sub.validation_report.status === 'Warning' ? 'text-amber-400' : 'text-rose-400'
                          }`} />
                          <span className={
                            sub.validation_report.status === 'Passed' ? 'text-emerald-400' :
                            sub.validation_report.status === 'Warning' ? 'text-amber-400' : 'text-rose-400'
                          }>
                            {sub.validation_report.score}/100
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-500 font-semibold italic">Unchecked</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        to={`/submissions/${sub.id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/60 rounded-md font-semibold text-[10px] transition-all"
                      >
                        Verify Docs
                        <ChevronRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Application Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="relative w-full max-w-md bg-[#0a0e1a] border border-slate-800 rounded-xl p-6 shadow-2xl space-y-4">
            <h2 className="text-base font-bold text-slate-100">Initialize Visa Application</h2>
            
            {mutationError && (
              <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-lg text-center font-medium">
                {mutationError}
              </div>
            )}

            {clients.length === 0 ? (
              <div className="text-center py-4 space-y-2">
                <p className="text-xs text-slate-400">There are no clients in the database. Please add a client first.</p>
                <button
                  type="button"
                  onClick={() => { setModalOpen(false); navigate('/clients'); }}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg py-1.5 px-3 font-semibold text-xs cursor-pointer"
                >
                  Go to Clients Page
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                {/* Select Client */}
                <div>
                  <label className="block text-[10px] font-semibold text-slate-400 mb-1">Select Client</label>
                  <select
                    {...register('client', { required: 'Client is required' })}
                    className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-300 transition-all cursor-pointer font-medium"
                  >
                    <option value="">-- Choose Client --</option>
                    {clients.map(c => (
                      <option key={c.id} value={c.id}>{c.name} ({c.passport_number})</option>
                    ))}
                  </select>
                  {errors.client && <p className="text-rose-400 text-[9px] mt-1 font-semibold">{errors.client.message as string}</p>}
                </div>

                {/* Country Selection */}
                <div>
                  <label className="block text-[10px] font-semibold text-slate-400 mb-1">Destination Country</label>
                  <select
                    {...register('country', { required: 'Country is required' })}
                    className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-300 transition-all cursor-pointer font-medium"
                  >
                    <option value="Canada">Canada</option>
                    <option value="UK">UK</option>
                    <option value="USA">USA</option>
                  </select>
                </div>

                {/* Visa Type Selection */}
                <div>
                  <label className="block text-[10px] font-semibold text-slate-400 mb-1">Visa Category</label>
                  <select
                    {...register('visa_type', { required: 'Visa type is required' })}
                    className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-300 transition-all cursor-pointer font-medium"
                  >
                    <option value="Tourist">Tourist</option>
                    <option value="Tourist">B1/B2</option>
                  </select>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-3 pt-3 border-t border-slate-800/60">
                  <button
                    type="button"
                    onClick={() => setModalOpen(false)}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 rounded-lg py-2 px-4 font-semibold text-xs cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createSubmissionMutation.isPending}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg py-2 px-4 font-semibold text-xs cursor-pointer flex items-center gap-1"
                  >
                    {createSubmissionMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    Initialize Case
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
