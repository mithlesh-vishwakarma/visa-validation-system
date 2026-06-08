import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import api from '../services/api';
import type { CountryRule, User } from '../types';
import { 
  Plus, 
  Users, 
  Globe, 
  ShieldCheck, 
  UserPlus, 
  Loader2,
  Trash2,
  Lock
} from 'lucide-react';

export default function Admin() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'rules' | 'users'>('rules');
  const [userError, setUserError] = useState('');
  const [ruleError, setRuleError] = useState('');
  
  // Modals
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [ruleModalOpen, setRuleModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<CountryRule | null>(null);

  // Forms
  const { register: regUser, handleSubmit: handleUserSubmit, reset: resetUser } = useForm();
  const { register: regRule, handleSubmit: handleRuleSubmit, setValue: setRuleValue, reset: resetRule } = useForm();

  // Queries
  const { data: rules = [], isLoading: loadingRules } = useQuery<CountryRule[]>({
    queryKey: ['country-rules'],
    queryFn: async () => {
      const response = await api.get('country-rules/');
      return response.data;
    }
  });

  const { data: orgUsers = [], isLoading: loadingUsers } = useQuery<User[]>({
    queryKey: ['org-users'],
    queryFn: async () => {
      const response = await api.get('org-users/');
      return response.data;
    }
  });

  // Mutations
  const inviteUserMutation = useMutation({
    mutationFn: async (payload: any) => {
      const response = await api.post('org-users/', payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['org-users'] });
      setUserModalOpen(false);
      resetUser();
    },
    onError: (err: any) => {
      setUserError(err.response?.data?.email?.join(', ') || err.response?.data?.detail || 'Failed to invite user.');
    }
  });

  const manageRuleMutation = useMutation({
    mutationFn: async (payload: any) => {
      if (editingRule) {
        const response = await api.put(`country-rules/${editingRule.id}/`, payload);
        return response.data;
      } else {
        const response = await api.post('country-rules/', payload);
        return response.data;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['country-rules'] });
      setRuleModalOpen(false);
      setEditingRule(null);
      resetRule();
    },
    onError: (err: any) => {
      setRuleError(err.response?.data?.detail || 'Failed to save rule. Ensure rule is unique for country/type.');
    }
  });

  const deleteRuleMutation = useMutation({
    mutationFn: async (ruleId: string) => {
      await api.delete(`country-rules/${ruleId}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['country-rules'] });
    }
  });

  const onUserSubmit = (data: any) => {
    setUserError('');
    inviteUserMutation.mutate(data);
  };

  const onRuleSubmit = (data: any) => {
    setRuleError('');
    // Split and clean required documents input
    const docList = data.required_documents.split(',').map((d: string) => d.trim()).filter((d: string) => d);
    const payload = {
      country: data.country,
      visa_type: data.visa_type,
      required_documents: docList,
      rules: {
        passport_min_validity_months: parseInt(data.passport_min_validity_months) || 6,
        min_bank_balance: parseFloat(data.min_bank_balance) || 300000
      }
    };
    manageRuleMutation.mutate(payload);
  };

  const openEditRule = (rule: CountryRule) => {
    setRuleError('');
    setEditingRule(rule);
    setRuleValue('country', rule.country);
    setRuleValue('visa_type', rule.visa_type);
    setRuleValue('required_documents', rule.required_documents.join(', '));
    setRuleValue('passport_min_validity_months', rule.rules.passport_min_validity_months || 6);
    setRuleValue('min_bank_balance', rule.rules.min_bank_balance || 300000);
    setRuleModalOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100 font-sans">Settings & Administration</h1>
        <p className="text-xs text-slate-400">Configure client compliance criteria and manage user workspace permissions.</p>
      </div>

      {/* Tabs Menu */}
      <div className="flex border-b border-slate-800/80">
        <button
          onClick={() => setActiveTab('rules')}
          className={`flex items-center gap-2 px-5 py-3 text-xs font-bold transition-all border-b-2 cursor-pointer ${
            activeTab === 'rules' 
              ? 'border-indigo-500 text-indigo-400 font-bold' 
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Globe className="w-4 h-4" />
          Country Visa Rules
        </button>
        <button
          onClick={() => setActiveTab('users')}
          className={`flex items-center gap-2 px-5 py-3 text-xs font-bold transition-all border-b-2 cursor-pointer ${
            activeTab === 'users' 
              ? 'border-indigo-500 text-indigo-400 font-bold' 
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Users className="w-4 h-4" />
          Team Members / Staff
        </button>
      </div>

      {/* Rules Tab */}
      {activeTab === 'rules' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-sm font-bold text-slate-200">Visa Evaluation Parameters</h2>
            <button
              onClick={() => { setEditingRule(null); setRuleError(''); resetRule(); setRuleModalOpen(true); }}
              className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg py-2 px-3.5 font-semibold text-xs transition-all flex items-center gap-1 shadow-lg shadow-indigo-600/10 cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Country Rule
            </button>
          </div>

          {loadingRules ? (
            <div className="flex justify-center py-8 text-slate-400">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {rules.map((rule) => (
                <div key={rule.id} className="p-4 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl hover-card-trigger flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start mb-2.5">
                      <div>
                        <h3 className="text-xs font-bold text-slate-200">{rule.country}</h3>
                        <span className="text-[10px] text-slate-500 font-semibold">{rule.visa_type} Category</span>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => openEditRule(rule)}
                          className="text-[10px] font-semibold text-indigo-400 hover:text-indigo-300 bg-indigo-500/5 px-2 py-1 rounded border border-indigo-500/10 cursor-pointer"
                        >
                          Modify
                        </button>
                        <button
                          onClick={() => deleteRuleMutation.mutate(rule.id)}
                          className="p-1 hover:bg-rose-500/10 text-slate-500 hover:text-rose-400 rounded transition-all cursor-pointer"
                          title="Delete rule"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div className="space-y-2 text-xs py-2.5 border-t border-slate-800/40">
                      <div>
                        <span className="text-[9px] font-bold text-slate-500 uppercase block mb-1">Required Documents</span>
                        <div className="flex flex-wrap gap-1.5">
                          {rule.required_documents.map((doc: string, i: number) => (
                            <span key={i} className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-slate-800/80 border border-slate-700 text-slate-300">
                              {doc}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-2 pt-1">
                        <div>
                          <span className="text-[9px] font-bold text-slate-500 uppercase block mb-0.5">Passport Validity</span>
                          <span className="font-semibold text-slate-300 text-[10px]">{rule.rules.passport_min_validity_months || 6} months</span>
                        </div>
                        <div>
                          <span className="text-[9px] font-bold text-slate-500 uppercase block mb-0.5">Min Bank Balance</span>
                          <span className="font-semibold text-slate-300 text-[10px]">₹{(rule.rules.min_bank_balance || 300000).toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-sm font-bold text-slate-200">Organization Staff Registry</h2>
            <button
              onClick={() => { setUserError(''); resetUser(); setUserModalOpen(true); }}
              className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg py-2 px-3.5 font-semibold text-xs transition-all flex items-center gap-1 shadow-lg shadow-indigo-600/10 cursor-pointer"
            >
              <UserPlus className="w-3.5 h-3.5" />
              Invite Team Member
            </button>
          </div>

          {loadingUsers ? (
            <div className="flex justify-center py-8 text-slate-400">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
          ) : (
            <div className="bg-[#0a0e1a]/85 border border-slate-800/60 rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-[10px] font-bold text-slate-400 uppercase tracking-wider bg-slate-900/30">
                      <th className="py-3.5 px-4">Staff Member</th>
                      <th className="py-3.5 px-4">Role</th>
                      <th className="py-3.5 px-4">Date Joined</th>
                      <th className="py-3.5 px-4">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40 text-xs text-slate-300">
                    {orgUsers.map((u) => (
                      <tr key={u.id} className="hover:bg-slate-800/10">
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-3">
                            <div className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center font-bold text-indigo-400 border border-slate-700">
                              {u.first_name ? u.first_name[0].toUpperCase() : u.email[0].toUpperCase()}
                            </div>
                            <div>
                              <div className="font-semibold text-slate-200">
                                {u.first_name ? `${u.first_name} ${u.last_name}` : 'Staff Member'}
                              </div>
                              <div className="text-[10px] text-slate-500 font-semibold">{u.email}</div>
                            </div>
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="flex items-center gap-1.5">
                            <ShieldCheck className="w-4 h-4 text-indigo-400" />
                            <span className="font-semibold">{u.role}</span>
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-slate-450">{new Date(u.date_joined).toLocaleDateString()}</td>
                        <td className="py-3.5 px-4">
                          <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold border ${
                            u.is_active ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-400' : 'bg-rose-500/5 border-rose-500/20 text-rose-400'
                          }`}>
                            {u.is_active ? 'Active' : 'Suspended'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Invite User Modal */}
      {userModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="relative w-full max-w-sm bg-[#0a0e1a] border border-slate-800 rounded-xl p-6 shadow-2xl space-y-4">
            <h2 className="text-sm font-bold text-slate-100">Invite Team Member</h2>
            
            {userError && (
              <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-lg text-center font-semibold">
                {userError}
              </div>
            )}

            <form onSubmit={handleUserSubmit(onUserSubmit)} className="space-y-3">
              <div>
                <label className="block text-[9px] font-bold text-slate-500 uppercase mb-1">First Name</label>
                <input
                  type="text"
                  {...regUser('first_name', { required: 'First name is required' })}
                  placeholder="Rahul"
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-100 placeholder-slate-500 transition-all"
                />
              </div>

              <div>
                <label className="block text-[9px] font-bold text-slate-500 uppercase mb-1">Last Name</label>
                <input
                  type="text"
                  {...regUser('last_name', { required: 'Last name is required' })}
                  placeholder="Sharma"
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-100 placeholder-slate-500 transition-all"
                />
              </div>

              <div>
                <label className="block text-[9px] font-bold text-slate-500 uppercase mb-1">Email Address</label>
                <input
                  type="email"
                  {...regUser('email', { required: 'Email is required' })}
                  placeholder="rahul@agency.com"
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-100 placeholder-slate-500 transition-all"
                />
              </div>

              <div>
                <label className="block text-[9px] font-bold text-slate-500 uppercase mb-1">Temporary Password</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                    <Lock className="w-3.5 h-3.5" />
                  </span>
                  <input
                    type="password"
                    {...regUser('password', { required: 'Password is required' })}
                    placeholder="••••••••"
                    className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:outline-none rounded-lg py-2 pl-9 pr-3 text-xs text-slate-100 placeholder-slate-500 transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[9px] font-bold text-slate-500 uppercase mb-1">Access Role</label>
                <select
                  {...regUser('role')}
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-300 transition-all cursor-pointer font-semibold"
                >
                  <option value="STAFF">Staff User</option>
                  <option value="AGENCY_ADMIN">Agency Admin</option>
                </select>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800/60">
                <button
                  type="button"
                  onClick={() => setUserModalOpen(false)}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 rounded-lg py-1.5 px-3 font-semibold text-xs cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={inviteUserMutation.isPending}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg py-1.5 px-3 font-semibold text-xs cursor-pointer flex items-center gap-1"
                >
                  {inviteUserMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  Add User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add/Edit Rule Modal */}
      {ruleModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="relative w-full max-w-sm bg-[#0a0e1a] border border-slate-800 rounded-xl p-6 shadow-2xl space-y-4">
            <h2 className="text-sm font-bold text-slate-100">{editingRule ? 'Modify Country Rule' : 'Add Country Rule'}</h2>
            
            {ruleError && (
              <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-lg text-center font-semibold">
                {ruleError}
              </div>
            )}

            <form onSubmit={handleRuleSubmit(onRuleSubmit)} className="space-y-3">
              <div>
                <label className="block text-[9px] font-bold text-slate-500 uppercase mb-1">Country</label>
                <input
                  type="text"
                  disabled={!!editingRule}
                  {...regRule('country', { required: 'Country is required' })}
                  placeholder="Canada"
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-100 placeholder-slate-500 transition-all disabled:opacity-40"
                />
              </div>

              <div>
                <label className="block text-[9px] font-bold text-slate-500 uppercase mb-1">Visa Category</label>
                <input
                  type="text"
                  disabled={!!editingRule}
                  {...regRule('visa_type', { required: 'Visa type is required' })}
                  placeholder="Tourist"
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-100 placeholder-slate-500 transition-all disabled:opacity-40"
                />
              </div>

              <div>
                <label className="block text-[9px] font-bold text-slate-500 uppercase mb-1">Required Documents (Comma-separated)</label>
                <input
                  type="text"
                  {...regRule('required_documents', { required: 'Docs are required' })}
                  placeholder="Passport, Bank Statement, ITR, Photo"
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-100 placeholder-slate-500 transition-all"
                />
              </div>

              <div>
                <label className="block text-[9px] font-bold text-slate-500 uppercase mb-1">Passport Min Validity (Months)</label>
                <input
                  type="number"
                  {...regRule('passport_min_validity_months', { required: 'Validity limit is required' })}
                  placeholder="6"
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-100 placeholder-slate-500 transition-all"
                />
              </div>

              <div>
                <label className="block text-[9px] font-bold text-slate-500 uppercase mb-1">Min Bank Balance Threshold (INR)</label>
                <input
                  type="number"
                  {...regRule('min_bank_balance', { required: 'Balance limit is required' })}
                  placeholder="300000"
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-100 placeholder-slate-500 transition-all"
                />
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800/60">
                <button
                  type="button"
                  onClick={() => setRuleModalOpen(false)}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 rounded-lg py-1.5 px-3 font-semibold text-xs cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={manageRuleMutation.isPending}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg py-1.5 px-3 font-semibold text-xs cursor-pointer flex items-center gap-1"
                >
                  {manageRuleMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  Save Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
