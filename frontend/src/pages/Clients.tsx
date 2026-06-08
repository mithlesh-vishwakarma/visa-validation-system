import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import api from '../services/api';
import type { Client } from '../types';
import { 
  Plus, 
  Search, 
  Loader2, 
  Mail, 
  Phone, 
  FilePlus, 
  Globe, 
  Layers
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Clients() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [search, setSearch] = React.useState('');
  const [modalOpen, setModalOpen] = React.useState(false);
  const [mutationError, setMutationError] = React.useState('');

  const { register, handleSubmit, reset, formState: { errors } } = useForm();

  // Fetch Clients
  const { data: clients = [], isLoading, error } = useQuery<Client[]>({
    queryKey: ['clients'],
    queryFn: async () => {
      const response = await api.get('clients/');
      return response.data;
    }
  });

  // Create Client Mutation
  const createClientMutation = useMutation({
    mutationFn: async (newClient: any) => {
      const response = await api.post('clients/', newClient);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      setModalOpen(false);
      reset();
      // Auto-trigger creating a visa application for this new client
      navigate('/submissions', { state: { createForClient: data } });
    },
    onError: (err: any) => {
      setMutationError(err.response?.data?.detail || 'Failed to create client. Please review input.');
    }
  });

  const onSubmit = (data: any) => {
    setMutationError('');
    createClientMutation.mutate(data);
  };

  const filteredClients = clients.filter(client => 
    client.name.toLowerCase().includes(search.toLowerCase()) ||
    client.passport_number.toLowerCase().includes(search.toLowerCase()) ||
    client.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Clients</h1>
          <p className="text-xs text-slate-400">Manage your agency clients and initialize visa document submissions.</p>
        </div>
        <button
          onClick={() => { setMutationError(''); setModalOpen(true); }}
          className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg py-2.5 px-4 font-semibold text-xs transition-all duration-150 flex items-center gap-1.5 cursor-pointer shadow-lg shadow-indigo-600/10 hover:shadow-indigo-600/20"
        >
          <Plus className="w-4 h-4" />
          Add Client
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex items-center bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl px-3.5 py-2">
        <Search className="w-4 h-4 text-slate-500 mr-2.5" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search clients by name, passport number, email..."
          className="bg-transparent border-0 focus:outline-none w-full text-xs text-slate-100 placeholder-slate-500"
        />
      </div>

      {isLoading ? (
        <div className="flex h-[40vh] items-center justify-center text-slate-400">
          <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mr-3" />
          <span>Loading client directory...</span>
        </div>
      ) : error ? (
        <div className="p-6 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm rounded-xl text-center">
          Failed to fetch client profiles. Check connection.
        </div>
      ) : filteredClients.length === 0 ? (
        <div className="p-12 bg-[#0a0e1a]/40 border border-slate-800/50 rounded-xl text-center">
          <p className="text-sm font-semibold text-slate-400">No clients found</p>
          <p className="text-xs text-slate-500 mt-1">Try refining search parameters or register a new client profile.</p>
        </div>
      ) : (
        /* Client Cards Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredClients.map((client) => (
            <div 
              key={client.id} 
              className="p-5 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl hover-card-trigger flex flex-col justify-between"
            >
              <div>
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h2 className="text-sm font-bold text-slate-200">{client.name}</h2>
                    <span className="text-[10px] font-semibold text-indigo-400 uppercase tracking-wider">{client.passport_number}</span>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[8px] font-bold border ${
                    client.status === 'Approved' ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-400' :
                    client.status === 'Rejected' ? 'bg-rose-500/5 border-rose-500/20 text-rose-400' :
                    client.status === 'Pending' ? 'bg-amber-500/5 border-amber-500/20 text-amber-400' :
                    'bg-slate-800 border-slate-700 text-slate-400'
                  }`}>
                    {client.status}
                  </span>
                </div>

                <div className="space-y-2 text-xs text-slate-400 py-3 border-y border-slate-800/40 my-3">
                  <div className="flex items-center gap-2">
                    <Mail className="w-3.5 h-3.5 text-slate-500" />
                    <span>{client.email}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone className="w-3.5 h-3.5 text-slate-500" />
                    <span>{client.mobile}</span>
                  </div>
                  <div className="flex items-center gap-4 pt-1 text-[11px] font-medium text-slate-300">
                    <span className="flex items-center gap-1">
                      <Globe className="w-3.5 h-3.5 text-indigo-400/80" />
                      {client.country}
                    </span>
                    <span className="flex items-center gap-1">
                      <Layers className="w-3.5 h-3.5 text-violet-400/80" />
                      {client.visa_type}
                    </span>
                  </div>
                </div>

                {client.notes && (
                  <p className="text-[10px] text-slate-500 italic line-clamp-2 mb-4">
                    "{client.notes}"
                  </p>
                )}
              </div>

              <div className="pt-2">
                <button
                  onClick={() => navigate('/submissions', { state: { createForClient: client } })}
                  className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/60 rounded-lg py-2 px-3 font-semibold text-xs transition-all duration-150 flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <FilePlus className="w-3.5 h-3.5" />
                  Apply for Visa
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Client Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="relative w-full max-w-lg bg-[#0a0e1a] border border-slate-800 rounded-xl p-6 shadow-2xl space-y-4">
            <h2 className="text-base font-bold text-slate-100">Create Client Profile</h2>
            
            {mutationError && (
              <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-lg text-center font-medium">
                {mutationError}
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Full Name */}
              <div className="sm:col-span-2">
                <label className="block text-[10px] font-semibold text-slate-400 mb-1">Full Name</label>
                <input
                  type="text"
                  {...register('name', { required: 'Name is required' })}
                  placeholder="Rahul Sharma"
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-100 placeholder-slate-500 transition-all"
                />
                {errors.name && <p className="text-rose-400 text-[9px] mt-1 font-semibold">{errors.name.message as string}</p>}
              </div>

              {/* Passport Number */}
              <div>
                <label className="block text-[10px] font-semibold text-slate-400 mb-1">Passport Number</label>
                <input
                  type="text"
                  {...register('passport_number', { required: 'Passport number is required' })}
                  placeholder="Z1234567"
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-100 placeholder-slate-500 transition-all"
                />
                {errors.passport_number && <p className="text-rose-400 text-[9px] mt-1 font-semibold">{errors.passport_number.message as string}</p>}
              </div>

              {/* Email */}
              <div>
                <label className="block text-[10px] font-semibold text-slate-400 mb-1">Email Address</label>
                <input
                  type="email"
                  {...register('email', { required: 'Email is required' })}
                  placeholder="rahul@domain.com"
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-100 placeholder-slate-500 transition-all"
                />
                {errors.email && <p className="text-rose-400 text-[9px] mt-1 font-semibold">{errors.email.message as string}</p>}
              </div>

              {/* Destination Country */}
              <div>
                <label className="block text-[10px] font-semibold text-slate-400 mb-1">Destination Country</label>
                <select
                  {...register('country', { required: 'Country is required' })}
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-300 transition-all cursor-pointer"
                >
                  <option value="Canada">Canada</option>
                  <option value="UK">UK</option>
                  <option value="USA">USA</option>
                </select>
              </div>

              {/* Visa Type */}
              <div>
                <label className="block text-[10px] font-semibold text-slate-400 mb-1">Visa Type</label>
                <select
                  {...register('visa_type', { required: 'Visa type is required' })}
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-300 transition-all cursor-pointer"
                >
                  <option value="Tourist">Tourist</option>
                  <option value="Tourist">B1/B2</option>
                </select>
              </div>

              {/* Mobile */}
              <div className="sm:col-span-2">
                <label className="block text-[10px] font-semibold text-slate-400 mb-1">Mobile Number</label>
                <input
                  type="text"
                  {...register('mobile', { required: 'Mobile is required' })}
                  placeholder="+91 98765 43210"
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-100 placeholder-slate-500 transition-all"
                />
                {errors.mobile && <p className="text-rose-400 text-[9px] mt-1 font-semibold">{errors.mobile.message as string}</p>}
              </div>

              {/* Notes */}
              <div className="sm:col-span-2">
                <label className="block text-[10px] font-semibold text-slate-400 mb-1">Internal Notes</label>
                <textarea
                  {...register('notes')}
                  placeholder="Additional consulting notes..."
                  rows={2}
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-100 placeholder-slate-500 transition-all resize-none"
                />
              </div>

              {/* Actions */}
              <div className="sm:col-span-2 flex justify-end gap-3 pt-3 border-t border-slate-800/60">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 rounded-lg py-2 px-4 font-semibold text-xs cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createClientMutation.isPending}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg py-2 px-4 font-semibold text-xs cursor-pointer flex items-center gap-1"
                >
                  {createClientMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  Register & Continue
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
