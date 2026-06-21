import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import api, { downloadReport } from '../services/api';
import type { Submission } from '../types';
import RiskBadge from '../components/RiskBadge';
import { Download, Loader2, FileText, Search, Filter, ExternalLink } from 'lucide-react';

export default function Reports() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const { data: submissions = [], isLoading } = useQuery<Submission[]>({
    queryKey: ['submissions-reports'],
    queryFn: async () => {
      const response = await api.get('submissions/');
      return response.data;
    },
    refetchInterval: 15000,
  });

  // Filter submissions that have validation reports (reportable)
  const reportable = submissions.filter((s) => {
    const matchSearch =
      !search ||
      s.client_detail?.name?.toLowerCase().includes(search.toLowerCase()) ||
      s.application_id?.toLowerCase().includes(search.toLowerCase()) ||
      s.country?.toLowerCase().includes(search.toLowerCase());

    const matchStatus = !statusFilter || s.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const handleDownload = async (s: Submission) => {
    if (!s.validation_report) {
      alert('No report available. Run rules validation first.');
      return;
    }
    setDownloadingId(s.id);
    try {
      await downloadReport(s.id, s.application_id);
    } catch {
      alert('Download failed.');
    } finally {
      setDownloadingId(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Approved': return { color: '#10b981', bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.25)' };
      case 'Rejected': return { color: '#ef4444', bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.25)' };
      case 'Under Review': return { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.25)' };
      case 'Pending': return { color: '#818cf8', bg: 'rgba(129,140,248,0.1)', border: 'rgba(129,140,248,0.25)' };
      default: return { color: '#94a3b8', bg: 'rgba(148,163,184,0.1)', border: 'rgba(148,163,184,0.2)' };
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[60vh] items-center justify-center text-slate-400">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mr-3" />
        <span>Loading reports...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Reports</h1>
        <p className="text-xs text-slate-400 mt-1">
          Download PDF eligibility reports for all visa applications.
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Total Applications', value: submissions.length, color: '#818cf8' },
          { label: 'Reports Available', value: submissions.filter((s) => s.validation_report).length, color: '#10b981' },
          { label: 'AI Assessed', value: submissions.filter((s) => s.eligibility_score).length, color: '#a78bfa' },
          { label: 'High Risk', value: submissions.filter((s) => s.eligibility_score?.risk_level === 'HIGH').length, color: '#ef4444' },
        ].map(({ label, value, color }) => (
          <div key={label} style={{
            background: 'rgba(15,23,42,0.8)',
            border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: 14,
            padding: '18px 20px',
          }}>
            <div style={{ fontSize: 28, fontWeight: 700, color }}>{value}</div>
            <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{
        background: 'rgba(15,23,42,0.8)',
        border: '1px solid rgba(255,255,255,0.07)',
        borderRadius: 14,
        padding: 20,
      }}>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search by name, application ID, or country..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:outline-none rounded-lg text-sm text-slate-300 placeholder-slate-600"
            />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="pl-9 pr-6 py-2.5 bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:outline-none rounded-lg text-sm text-slate-300 cursor-pointer"
            >
              <option value="">All Statuses</option>
              <option value="Approved">Approved</option>
              <option value="Rejected">Rejected</option>
              <option value="Under Review">Under Review</option>
              <option value="Pending">Pending</option>
              <option value="Draft">Draft</option>
            </select>
          </div>
        </div>
      </div>

      {/* Reports Table */}
      <div style={{
        background: 'rgba(15,23,42,0.8)',
        border: '1px solid rgba(255,255,255,0.07)',
        borderRadius: 14,
        overflow: 'hidden',
      }}>
        {reportable.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-500">
            <FileText className="w-12 h-12 mb-4 opacity-30" />
            <p className="font-semibold text-slate-400">No applications found</p>
            <p className="text-sm mt-1">Try adjusting your search or filters</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(0,0,0,0.2)' }}>
                {['Application', 'Client', 'Destination', 'Status', 'AI Score', 'Risk', 'Report', 'Actions'].map((h) => (
                  <th key={h} style={{
                    padding: '12px 16px',
                    textAlign: 'left',
                    fontSize: 11,
                    fontWeight: 700,
                    color: '#64748b',
                    letterSpacing: '0.05em',
                    textTransform: 'uppercase',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {reportable.map((s, idx) => {
                const statusCfg = getStatusColor(s.status);
                const hasReport = !!s.validation_report;
                const aiScore = s.eligibility_score?.final_score;
                const isDownloading = downloadingId === s.id;
                return (
                  <tr
                    key={s.id}
                    style={{
                      borderBottom: idx < reportable.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                      background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)',
                      transition: 'background 0.15s',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(99,102,241,0.05)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)')}
                  >
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{ fontSize: 12, fontWeight: 700, color: '#818cf8' }}>
                        {s.application_id}
                      </span>
                      <div style={{ fontSize: 10, color: '#64748b', marginTop: 2 }}>
                        {new Date(s.created_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>
                        {s.client_detail?.name}
                      </div>
                      <div style={{ fontSize: 11, color: '#64748b' }}>{s.client_detail?.email}</div>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ fontSize: 12, color: '#cbd5e1' }}>{s.country}</div>
                      <div style={{ fontSize: 11, color: '#64748b' }}>{s.visa_type}</div>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{
                        padding: '3px 10px',
                        borderRadius: 99,
                        fontSize: 11,
                        fontWeight: 700,
                        color: statusCfg.color,
                        background: statusCfg.bg,
                        border: `1px solid ${statusCfg.border}`,
                      }}>
                        {s.status}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      {aiScore !== undefined ? (
                        <span style={{
                          fontSize: 15,
                          fontWeight: 700,
                          color: aiScore >= 70 ? '#10b981' : aiScore >= 50 ? '#f59e0b' : '#ef4444',
                        }}>
                          {aiScore}<span style={{ fontSize: 10, color: '#64748b' }}>/100</span>
                        </span>
                      ) : (
                        <span style={{ fontSize: 11, color: '#64748b' }}>—</span>
                      )}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      {s.eligibility_score ? (
                        <RiskBadge risk={s.eligibility_score.risk_level} size="sm" />
                      ) : (
                        <span style={{ fontSize: 11, color: '#64748b' }}>—</span>
                      )}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{
                        fontSize: 11,
                        fontWeight: 600,
                        color: hasReport ? '#10b981' : '#64748b',
                      }}>
                        {hasReport ? '✓ Ready' : '○ Pending'}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <div className="flex items-center gap-2">
                        <Link
                          to={`/submissions/${s.id}`}
                          style={{
                            padding: '5px 10px',
                            borderRadius: 6,
                            fontSize: 11,
                            fontWeight: 600,
                            color: '#818cf8',
                            background: 'rgba(129,140,248,0.1)',
                            border: '1px solid rgba(129,140,248,0.2)',
                            textDecoration: 'none',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 4,
                          }}
                        >
                          <ExternalLink style={{ width: 12, height: 12 }} />
                          View
                        </Link>
                        <button
                          onClick={() => handleDownload(s)}
                          disabled={!hasReport || isDownloading}
                          style={{
                            padding: '5px 10px',
                            borderRadius: 6,
                            fontSize: 11,
                            fontWeight: 600,
                            color: hasReport ? '#e2e8f0' : '#475569',
                            background: hasReport ? 'rgba(255,255,255,0.07)' : 'transparent',
                            border: `1px solid ${hasReport ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.05)'}`,
                            cursor: hasReport ? 'pointer' : 'not-allowed',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 4,
                            opacity: !hasReport ? 0.5 : 1,
                          }}
                        >
                          {isDownloading ? (
                            <Loader2 style={{ width: 12, height: 12, animation: 'spin 1s linear infinite' }} />
                          ) : (
                            <Download style={{ width: 12, height: 12 }} />
                          )}
                          PDF
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
