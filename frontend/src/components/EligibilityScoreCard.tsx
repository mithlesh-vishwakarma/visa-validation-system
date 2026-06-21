import React from 'react';
import type { EligibilityScore, EligibilityScoreBreakdown } from '../types';

interface EligibilityScoreCardProps {
  score: EligibilityScore;
}

const CATEGORY_CONFIG = [
  { key: 'financial', label: 'Financial Strength', icon: '💰', weight: '30%' },
  { key: 'employment', label: 'Employment Stability', icon: '💼', weight: '25%' },
  { key: 'travel_history', label: 'Travel History', icon: '✈️', weight: '15%' },
  { key: 'documentation', label: 'Documentation Quality', icon: '📄', weight: '15%' },
  { key: 'compliance', label: 'Rule Compliance', icon: '✅', weight: '15%' },
] as const;

const getScoreColor = (score: number) => {
  if (score >= 80) return '#10b981';
  if (score >= 60) return '#f59e0b';
  return '#ef4444';
};

const getScoreGradient = (score: number) => {
  if (score >= 80) return 'linear-gradient(90deg, #10b981, #059669)';
  if (score >= 60) return 'linear-gradient(90deg, #f59e0b, #d97706)';
  return 'linear-gradient(90deg, #ef4444, #dc2626)';
};

const getRiskConfig = (risk: string) => {
  switch (risk) {
    case 'LOW': return { color: '#10b981', bg: 'rgba(16,185,129,0.12)', label: 'Low Risk' };
    case 'MEDIUM': return { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', label: 'Medium Risk' };
    case 'HIGH': return { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', label: 'High Risk' };
    default: return { color: '#94a3b8', bg: 'rgba(148,163,184,0.12)', label: 'Unknown' };
  }
};

const ScoreRing: React.FC<{ score: number; size?: number }> = ({ score, size = 120 }) => {
  const radius = (size - 16) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  const color = getScoreColor(score);

  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={10}
        />
        {/* Score arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
        />
      </svg>
      {/* Center label */}
      <div style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <span style={{ fontSize: size > 100 ? 28 : 18, fontWeight: 700, color, lineHeight: 1 }}>{score}</span>
        <span style={{ fontSize: 10, color: '#94a3b8', marginTop: 2 }}>/ 100</span>
      </div>
    </div>
  );
};

const CategoryBar: React.FC<{
  label: string;
  icon: string;
  weight: string;
  score: number;
  breakdown?: EligibilityScoreBreakdown;
}> = ({ label, icon, weight, score, breakdown }) => {
  const color = getScoreColor(score);
  const gradient = getScoreGradient(score);

  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)',
      borderRadius: 12,
      padding: '14px 16px',
      border: '1px solid rgba(255,255,255,0.06)',
      marginBottom: 10,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 18 }}>{icon}</span>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>{label}</div>
            {breakdown?.detail && (
              <div style={{ fontSize: 11, color: '#64748b', marginTop: 2, maxWidth: 280, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {breakdown.detail}
              </div>
            )}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 11, color: '#64748b', fontWeight: 500 }}>weight {weight}</span>
          <div style={{
            fontSize: 16,
            fontWeight: 700,
            color,
            minWidth: 36,
            textAlign: 'right',
          }}>
            {score}
          </div>
        </div>
      </div>
      {/* Progress bar */}
      <div style={{ height: 6, background: 'rgba(255,255,255,0.08)', borderRadius: 99, overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${score}%`,
          background: gradient,
          borderRadius: 99,
          transition: 'width 0.8s cubic-bezier(0.4,0,0.2,1)',
        }} />
      </div>
    </div>
  );
};

const EligibilityScoreCard: React.FC<EligibilityScoreCardProps> = ({ score }) => {
  const riskConfig = getRiskConfig(score.risk_level);

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(15,23,42,0.95) 0%, rgba(30,41,59,0.95) 100%)',
      borderRadius: 20,
      border: '1px solid rgba(255,255,255,0.1)',
      padding: 24,
      backdropFilter: 'blur(20px)',
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 24, marginBottom: 28 }}>
        {/* Score ring */}
        <ScoreRing score={score.final_score} size={120} />

        {/* Score info */}
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
            <h3 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#f1f5f9' }}>
              AI Eligibility Assessment
            </h3>
            {/* Eligible badge */}
            <span style={{
              padding: '4px 12px',
              borderRadius: 99,
              fontSize: 12,
              fontWeight: 700,
              background: score.is_eligible ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
              color: score.is_eligible ? '#10b981' : '#ef4444',
              border: `1px solid ${score.is_eligible ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
            }}>
              {score.is_eligible ? '✓ ELIGIBLE' : '✗ NOT ELIGIBLE'}
            </span>
          </div>

          {/* Risk level */}
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            background: riskConfig.bg,
            border: `1px solid ${riskConfig.color}40`,
            borderRadius: 8,
            padding: '5px 12px',
            marginBottom: 12,
          }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: riskConfig.color }} />
            <span style={{ fontSize: 12, fontWeight: 600, color: riskConfig.color }}>{riskConfig.label}</span>
          </div>

          {/* Summary */}
          {score.eligibility_summary && (
            <p style={{
              margin: 0,
              fontSize: 13,
              color: '#94a3b8',
              lineHeight: 1.6,
              maxWidth: 480,
            }}>
              {score.eligibility_summary.slice(0, 200)}
              {score.eligibility_summary.length > 200 ? '...' : ''}
            </p>
          )}
        </div>
      </div>

      {/* Category Breakdown */}
      <div style={{ marginBottom: 20 }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: 13, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Score Breakdown
        </h4>
        {CATEGORY_CONFIG.map(({ key, label, icon, weight }) => {
          const catScore = score[`${key}_score` as keyof EligibilityScore] as number;
          const breakdown = score.weighted_breakdown?.[key as keyof typeof score.weighted_breakdown] as EligibilityScoreBreakdown | undefined;
          return (
            <CategoryBar
              key={key}
              label={label}
              icon={icon}
              weight={weight}
              score={catScore}
              breakdown={breakdown}
            />
          );
        })}
      </div>

      {/* Strengths */}
      {score.strengths && score.strengths.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <h4 style={{ margin: '0 0 10px 0', fontSize: 13, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Strengths
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {score.strengths.map((s, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 13, color: '#cbd5e1' }}>
                <span style={{ color: '#10b981', flexShrink: 0, marginTop: 1 }}>✓</span>
                <span>{s}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default EligibilityScoreCard;
