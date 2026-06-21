import React, { useState } from 'react';
import type { EligibilityScore, CrossValidationCheck, RiskFactor } from '../types';
import RiskBadge from './RiskBadge';

interface AIAnalysisPanelProps {
  eligibilityScore: EligibilityScore;
}

const CheckResult: React.FC<{ check: CrossValidationCheck }> = ({ check }) => {
  const config = {
    PASS: { color: '#10b981', bg: 'rgba(16,185,129,0.08)', icon: '✓', border: 'rgba(16,185,129,0.2)' },
    WARNING: { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', icon: '⚠', border: 'rgba(245,158,11,0.2)' },
    FAIL: { color: '#ef4444', bg: 'rgba(239,68,68,0.08)', icon: '✕', border: 'rgba(239,68,68,0.2)' },
  }[check.result];

  return (
    <div style={{
      background: config.bg,
      border: `1px solid ${config.border}`,
      borderRadius: 10,
      padding: '12px 14px',
      marginBottom: 8,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{
          width: 22,
          height: 22,
          borderRadius: '50%',
          background: config.color,
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 12,
          fontWeight: 700,
          flexShrink: 0,
        }}>{config.icon}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>{check.check}</div>
          <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 3, lineHeight: 1.5 }}>{check.detail}</div>
        </div>
        <span style={{
          fontSize: 11,
          fontWeight: 700,
          color: config.color,
          padding: '2px 8px',
          borderRadius: 4,
          background: config.bg,
          border: `1px solid ${config.border}`,
          flexShrink: 0,
        }}>{check.result}</span>
      </div>
    </div>
  );
};

const RiskFactorItem: React.FC<{ factor: RiskFactor }> = ({ factor }) => {
  const severityConfig = {
    HIGH: { color: '#ef4444', bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.2)' },
    MEDIUM: { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)' },
    LOW: { color: '#94a3b8', bg: 'rgba(148,163,184,0.06)', border: 'rgba(148,163,184,0.15)' },
  }[factor.severity];

  return (
    <div style={{
      background: severityConfig.bg,
      border: `1px solid ${severityConfig.border}`,
      borderRadius: 10,
      padding: '12px 14px',
      marginBottom: 8,
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
        <span style={{
          padding: '2px 8px',
          borderRadius: 4,
          fontSize: 10,
          fontWeight: 700,
          color: severityConfig.color,
          background: severityConfig.bg,
          border: `1px solid ${severityConfig.border}`,
          flexShrink: 0,
          letterSpacing: '0.05em',
        }}>{factor.severity}</span>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', marginBottom: 4 }}>{factor.factor}</div>
          <div style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.5 }}>{factor.detail}</div>
        </div>
      </div>
    </div>
  );
};

type TabId = 'cross-validation' | 'risk-factors' | 'recommendations';

const AIAnalysisPanel: React.FC<AIAnalysisPanelProps> = ({ eligibilityScore }) => {
  const [activeTab, setActiveTab] = useState<TabId>('cross-validation');

  const { cross_validation_results, risk_factors, recommendations } = eligibilityScore;
  const checks = cross_validation_results?.checks || [];

  const tabs: Array<{ id: TabId; label: string; count: number; badge?: string }> = [
    {
      id: 'cross-validation',
      label: 'Cross-Validation',
      count: checks.length,
      badge: cross_validation_results?.overall_status,
    },
    { id: 'risk-factors', label: 'Risk Factors', count: risk_factors?.length || 0 },
    { id: 'recommendations', label: 'Recommendations', count: recommendations?.length || 0 },
  ];

  const tabBadgeColor = (badge?: string) => {
    if (badge === 'PASS') return '#10b981';
    if (badge === 'WARNING') return '#f59e0b';
    if (badge === 'FAIL') return '#ef4444';
    return undefined;
  };

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(15,23,42,0.95) 0%, rgba(30,41,59,0.95) 100%)',
      borderRadius: 20,
      border: '1px solid rgba(255,255,255,0.1)',
      padding: 24,
      backdropFilter: 'blur(20px)',
    }}>
      <h3 style={{ margin: '0 0 18px 0', fontSize: 16, fontWeight: 700, color: '#f1f5f9' }}>
        🔍 AI Deep Analysis
      </h3>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, background: 'rgba(0,0,0,0.2)', borderRadius: 10, padding: 4 }}>
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                flex: 1,
                padding: '8px 12px',
                borderRadius: 8,
                border: 'none',
                cursor: 'pointer',
                background: isActive ? 'rgba(99,102,241,0.2)' : 'transparent',
                color: isActive ? '#818cf8' : '#64748b',
                fontWeight: isActive ? 700 : 500,
                fontSize: 13,
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 6,
              }}
            >
              {tab.label}
              <span style={{
                padding: '1px 7px',
                borderRadius: 99,
                fontSize: 11,
                fontWeight: 700,
                background: isActive
                  ? (tabBadgeColor(tab.badge) ? `${tabBadgeColor(tab.badge)}30` : 'rgba(99,102,241,0.2)')
                  : 'rgba(255,255,255,0.06)',
                color: isActive
                  ? (tabBadgeColor(tab.badge) || '#818cf8')
                  : '#64748b',
              }}>
                {tab.badge || tab.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div style={{ minHeight: 200 }}>
        {activeTab === 'cross-validation' && (
          <div>
            {checks.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#64748b', padding: 32 }}>
                No cross-validation data available. Run AI Assessment first.
              </div>
            ) : (
              <>
                {/* Summary row */}
                <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
                  {[
                    { label: 'Passed', value: cross_validation_results?.passed ?? 0, color: '#10b981' },
                    { label: 'Warnings', value: cross_validation_results?.warnings ?? 0, color: '#f59e0b' },
                    { label: 'Failed', value: cross_validation_results?.failed ?? 0, color: '#ef4444' },
                    { label: 'Consistency', value: `${cross_validation_results?.consistency_score ?? 0}%`, color: '#818cf8' },
                  ].map(({ label, value, color }) => (
                    <div key={label} style={{
                      flex: 1,
                      background: 'rgba(255,255,255,0.04)',
                      borderRadius: 10,
                      padding: '10px 14px',
                      textAlign: 'center',
                      border: '1px solid rgba(255,255,255,0.06)',
                    }}>
                      <div style={{ fontSize: 20, fontWeight: 700, color }}>{value}</div>
                      <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{label}</div>
                    </div>
                  ))}
                </div>
                {checks.map((check, i) => <CheckResult key={i} check={check} />)}
              </>
            )}
          </div>
        )}

        {activeTab === 'risk-factors' && (
          <div>
            {(!risk_factors || risk_factors.length === 0) ? (
              <div style={{
                textAlign: 'center',
                color: '#10b981',
                padding: 32,
                background: 'rgba(16,185,129,0.05)',
                borderRadius: 12,
                border: '1px solid rgba(16,185,129,0.15)',
              }}>
                <div style={{ fontSize: 32, marginBottom: 8 }}>✓</div>
                <div style={{ fontWeight: 600 }}>No significant risk factors identified</div>
                <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>Application appears clean.</div>
              </div>
            ) : (
              <div>
                {/* Risk breakdown */}
                <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
                  {(['HIGH', 'MEDIUM', 'LOW'] as const).map((severity) => {
                    const count = risk_factors.filter((r) => r.severity === severity).length;
                    const colors = { HIGH: '#ef4444', MEDIUM: '#f59e0b', LOW: '#94a3b8' };
                    return (
                      <div key={severity} style={{
                        flex: 1,
                        background: 'rgba(255,255,255,0.04)',
                        borderRadius: 10,
                        padding: '10px 14px',
                        textAlign: 'center',
                        border: '1px solid rgba(255,255,255,0.06)',
                      }}>
                        <div style={{ fontSize: 20, fontWeight: 700, color: colors[severity] }}>{count}</div>
                        <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{severity}</div>
                      </div>
                    );
                  })}
                </div>
                {/* Sorted: HIGH first */}
                {[...risk_factors]
                  .sort((a, b) => {
                    const order = { HIGH: 0, MEDIUM: 1, LOW: 2 };
                    return order[a.severity] - order[b.severity];
                  })
                  .map((factor, i) => <RiskFactorItem key={i} factor={factor} />)}
              </div>
            )}
          </div>
        )}

        {activeTab === 'recommendations' && (
          <div>
            {(!recommendations || recommendations.length === 0) ? (
              <div style={{ textAlign: 'center', color: '#64748b', padding: 32 }}>
                No recommendations available.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {recommendations.map((rec, i) => (
                  <div key={i} style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 12,
                    background: 'rgba(99,102,241,0.06)',
                    border: '1px solid rgba(99,102,241,0.15)',
                    borderRadius: 12,
                    padding: '14px 16px',
                  }}>
                    <div style={{
                      width: 26,
                      height: 26,
                      borderRadius: '50%',
                      background: 'rgba(99,102,241,0.2)',
                      color: '#818cf8',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 13,
                      fontWeight: 700,
                      flexShrink: 0,
                    }}>
                      {i + 1}
                    </div>
                    <p style={{ margin: 0, fontSize: 13, color: '#cbd5e1', lineHeight: 1.6 }}>{rec}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AIAnalysisPanel;
