import React from 'react';
import type { RiskLevel } from '../types';

interface RiskBadgeProps {
  risk: RiskLevel;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

const RISK_CONFIG: Record<RiskLevel, { color: string; bg: string; border: string; icon: string; label: string }> = {
  LOW: {
    color: '#10b981',
    bg: 'rgba(16,185,129,0.12)',
    border: 'rgba(16,185,129,0.3)',
    icon: '🟢',
    label: 'Low Risk',
  },
  MEDIUM: {
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.12)',
    border: 'rgba(245,158,11,0.3)',
    icon: '🟡',
    label: 'Medium Risk',
  },
  HIGH: {
    color: '#ef4444',
    bg: 'rgba(239,68,68,0.12)',
    border: 'rgba(239,68,68,0.3)',
    icon: '🔴',
    label: 'High Risk',
  },
};

const SIZE_MAP = {
  sm: { fontSize: 11, padding: '3px 8px', dotSize: 6 },
  md: { fontSize: 13, padding: '5px 12px', dotSize: 8 },
  lg: { fontSize: 15, padding: '8px 16px', dotSize: 10 },
};

const RiskBadge: React.FC<RiskBadgeProps> = ({ risk, size = 'md', showIcon = true }) => {
  const config = RISK_CONFIG[risk];
  const sizeConfig = SIZE_MAP[size];

  return (
    <span
      title={`Risk Level: ${config.label}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: sizeConfig.padding,
        borderRadius: 99,
        fontSize: sizeConfig.fontSize,
        fontWeight: 700,
        color: config.color,
        background: config.bg,
        border: `1px solid ${config.border}`,
        letterSpacing: '0.03em',
        whiteSpace: 'nowrap',
        userSelect: 'none',
      }}
    >
      {showIcon && (
        <span style={{
          width: sizeConfig.dotSize,
          height: sizeConfig.dotSize,
          borderRadius: '50%',
          background: config.color,
          display: 'inline-block',
          flexShrink: 0,
          boxShadow: `0 0 6px ${config.color}80`,
        }} />
      )}
      {config.label}
    </span>
  );
};

export default RiskBadge;
