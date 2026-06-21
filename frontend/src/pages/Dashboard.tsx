import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import type { DashboardData } from '../types';
import {
  Users,
  FileCheck,
  FileClock,
  FileWarning,
  Activity,
  Award,
  Globe,
  Loader2,
  TrendingUp,
  Brain,
  ShieldCheck,
  AlertOctagon
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar
} from 'recharts';

const COLORS = ['#6366f1', '#8b5cf6', '#3b82f6', '#ec4899', '#f59e0b', '#10b981'];

export default function Dashboard() {
  const { data, isLoading, error } = useQuery<DashboardData>({
    queryKey: ['dashboard-analytics'],
    queryFn: async () => {
      const response = await api.get('dashboard/analytics/');
      return response.data;
    },
    refetchInterval: 10000, // Refresh every 10s
  });

  if (isLoading) {
    return (
      <div className="flex h-[60vh] items-center justify-center text-slate-400">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mr-3" />
        <span>Loading dashboard analytics...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm rounded-xl text-center">
        Failed to fetch dashboard metrics. Please check network connection or contact administrator.
      </div>
    );
  }

  const { metrics, trends, countries, score_distribution, recent_activity } = data;

  const cardData = [
    { label: 'Total Clients', value: metrics.total_clients, icon: Users, color: 'text-sky-400', bg: 'bg-sky-500/5 border-sky-500/10' },
    { label: 'Total Applications', value: metrics.total_submissions, icon: TrendingUp, color: 'text-indigo-400', bg: 'bg-indigo-500/5 border-indigo-500/10' },
    { label: 'Approved Cases', value: metrics.approved, icon: FileCheck, color: 'text-emerald-400', bg: 'bg-emerald-500/5 border-emerald-500/10' },
    { label: 'Under Review / Pending', value: metrics.under_review + metrics.pending, icon: FileClock, color: 'text-amber-400', bg: 'bg-amber-500/5 border-amber-500/10' },
    { label: 'Rejected Cases', value: metrics.rejected, icon: FileWarning, color: 'text-rose-400', bg: 'bg-rose-500/5 border-rose-500/10' },
    { label: 'Avg Rules Score', value: `${metrics.avg_score}%`, icon: Award, color: 'text-violet-400', bg: 'bg-violet-500/5 border-violet-500/10' },
    // AI Metrics
    { label: 'AI Assessed', value: metrics.total_ai_assessed ?? 0, icon: Brain, color: 'text-purple-400', bg: 'bg-purple-500/5 border-purple-500/10' },
    { label: 'Avg AI Score', value: `${metrics.avg_eligibility_score ?? 0}`, icon: ShieldCheck, color: 'text-teal-400', bg: 'bg-teal-500/5 border-teal-500/10' },
    { label: 'High Risk', value: metrics.risk_distribution?.HIGH ?? 0, icon: AlertOctagon, color: 'text-rose-400', bg: 'bg-rose-500/5 border-rose-500/10' },
  ];

  const riskDistData = [
    { name: 'Low Risk', value: metrics.risk_distribution?.LOW ?? 0, color: '#10b981' },
    { name: 'Medium Risk', value: metrics.risk_distribution?.MEDIUM ?? 0, color: '#f59e0b' },
    { name: 'High Risk', value: metrics.risk_distribution?.HIGH ?? 0, color: '#ef4444' },
  ];


  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Overview</h1>
        <p className="text-xs text-slate-400">Visual dashboard for client statistics and document check compliance metrics.</p>
      </div>

      {/* Metric Cards Grid — 9 cards: 6 existing + 3 AI metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-9 gap-4">
        {cardData.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div key={idx} className={`p-4 rounded-xl border flex flex-col justify-between ${card.bg} hover-card-trigger`}>
              <div className="flex justify-between items-start mb-2">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">{card.label}</span>
                <Icon className={`w-4 h-4 ${card.color}`} />
              </div>
              <div className="text-xl font-bold text-slate-100">{card.value}</div>
            </div>
          );
        })}
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Area Chart */}
        <div className="lg:col-span-2 p-5 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-sm font-bold text-slate-200">Submission Compliance Trends</h2>
            <span className="text-[10px] text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700 font-semibold">2026 Monthly Data</span>
          </div>
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends} margin={{ top: 10, right: 5, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorSub" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorApp" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.15}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.3} />
                <XAxis dataKey="month" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={10} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f1f5f9', fontSize: 11 }}
                />
                <Area type="monotone" dataKey="submissions" name="Total Submissions" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorSub)" />
                <Area type="monotone" dataKey="approved" name="Approved Cases" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorApp)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Country Breakdown Pie Chart */}
        <div className="p-5 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-1.5">
              <Globe className="w-4 h-4 text-indigo-400" />
              Country-wise Distribution
            </h2>
            {countries.length === 0 ? (
              <div className="h-[180px] flex items-center justify-center text-xs text-slate-500">
                No submissions data available.
              </div>
            ) : (
              <div className="h-[180px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={countries}
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={70}
                      paddingAngle={3}
                      dataKey="value"
                      nameKey="country"
                    >
                      {countries.map((_entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f1f5f9', fontSize: 11 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs pt-4 border-t border-slate-800/60 max-h-[80px] overflow-y-auto">
            {countries.map((c, idx) => (
              <div key={idx} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                <span className="truncate text-slate-300 font-medium">{c.country}: <span className="text-slate-400 font-semibold">{c.value}</span></span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Score Distribution & Timeline Activity Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Score Distribution Bar Chart */}
        <div className="lg:col-span-1 p-5 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl">
          <h2 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-1.5">
            <Award className="w-4 h-4 text-indigo-400" />
            Validation Score Distribution
          </h2>
          <div className="h-[220px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={score_distribution} margin={{ left: -30, right: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.3} />
                <XAxis dataKey="range" stroke="#64748b" fontSize={9} />
                <YAxis stroke="#64748b" fontSize={10} allowDecimals={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f1f5f9', fontSize: 11 }} />
                <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]}>
                  {score_distribution.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.range.includes('Pass') ? '#10b981' : entry.range.includes('Warning') ? '#f59e0b' : '#ef4444'} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Audit Log / Activity Log Timeline */}
        <div className="lg:col-span-2 p-5 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl">
          <h2 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-1.5">
            <Activity className="w-4 h-4 text-indigo-400" />
            Audit Log / Activity Timeline
          </h2>
          <div className="space-y-4 max-h-[220px] overflow-y-auto pr-1">
            {recent_activity.length === 0 ? (
              <div className="text-center text-xs py-8 text-slate-500 font-semibold">
                No recent activity logged in organization.
              </div>
            ) : (
              recent_activity.map((log) => (
                <div key={log.id} className="relative flex gap-3 pb-3 border-b border-slate-800/40 last:border-0 last:pb-0">
                  <div className="w-7 h-7 rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center shrink-0">
                    <Activity className="w-3.5 h-3.5 text-indigo-400" />
                  </div>
                  <div className="flex-1 min-w-0 text-xs">
                    <div className="flex justify-between items-start mb-0.5">
                      <span className="font-bold text-slate-200">{log.action}</span>
                      <span className="text-[10px] text-slate-500 font-semibold">
                        {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="text-slate-400 leading-normal">
                      Client: <span className="font-semibold text-slate-300">{log.details.client_name || 'N/A'}</span> &bull; 
                      Country: <span className="font-semibold text-indigo-400">{log.details.country || 'N/A'}</span> &bull; 
                      Score: <span className="font-bold text-slate-300">{log.details.score ?? 'N/A'}</span>
                    </p>
                    <div className="text-[9px] text-slate-500 italic mt-0.5">
                      Performed by {log.user_email || 'System'} &bull; {new Date(log.timestamp).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
