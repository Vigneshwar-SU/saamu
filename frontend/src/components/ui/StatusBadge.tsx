import React from 'react';
import { Chip } from '@mui/material';

export type StatusTone = 'success' | 'warning' | 'error' | 'info' | 'gold' | 'neutral';

const TONE_STYLES: Record<StatusTone, { bg: string; text: string; border?: string }> = {
  success: { bg: '#E7F1EA', text: '#1F5C3C' },
  warning: { bg: '#FBF0E3', text: '#8F4A00' },
  error: { bg: '#FBE9E6', text: '#8F2F22' },
  info: { bg: '#EDE9DF', text: '#544A35' },
  gold: { bg: '#F5EBD2', text: '#7A5E0C', border: '#E8D79A' },
  neutral: { bg: '#F1EDE2', text: '#6B6B6B' },
};

interface StatusBadgeProps {
  label: string;
  tone?: StatusTone;
  icon?: React.ReactNode;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ label, tone = 'neutral', icon }) => {
  const styles = TONE_STYLES[tone] ?? TONE_STYLES.neutral;
  return (
    <Chip
      icon={icon as React.ReactElement | undefined}
      label={label}
      size="small"
      sx={{
        fontWeight: 600,
        backgroundColor: styles.bg,
        color: styles.text,
        border: styles.border ? `1px solid ${styles.border}` : '1px solid transparent',
        height: 26,
        '& .MuiChip-icon': {
          color: 'inherit',
          fontSize: 16,
        },
      }}
    />
  );
};

export default StatusBadge;
