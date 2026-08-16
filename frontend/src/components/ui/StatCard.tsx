import React from 'react';
import { Box, Card, Skeleton, Typography } from '@mui/material';

export type StatTone = 'default' | 'gold' | 'success' | 'warning' | 'error' | 'info';

const TONE_STYLES: Record<StatTone, { tileBg: string; tileColor: string; valueColor: string }> = {
  default: { tileBg: '#F1EDE2', tileColor: '#6B5E44', valueColor: '#242424' },
  gold: { tileBg: '#F5EBD2', tileColor: '#A98216', valueColor: '#242424' },
  success: { tileBg: '#E7F1EA', tileColor: '#2E7D52', valueColor: '#2E7D52' },
  warning: { tileBg: '#FBF0E3', tileColor: '#B25E00', valueColor: '#8F4A00' },
  error: { tileBg: '#FBE9E6', tileColor: '#B3402F', valueColor: '#8F2F22' },
  info: { tileBg: '#EDE9DF', tileColor: '#6B5E44', valueColor: '#242424' },
};

interface StatCardProps {
  label: string;
  value: string;
  sublabel?: string;
  icon?: React.ReactNode;
  tone?: StatTone;
  /** Legacy override — directly sets the value/icon color. */
  accent?: string;
  loading?: boolean;
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  sublabel,
  icon,
  tone = 'default',
  accent,
  loading = false,
  onClick,
}) => {
  const styles = TONE_STYLES[tone] ?? TONE_STYLES.default;
  const tileColor = accent ?? styles.tileColor;
  const valueColor = accent ?? styles.valueColor;

  return (
    <Card
      onClick={onClick}
      sx={{
        borderRadius: '14px',
        border: '1px solid #E7E0D0',
        boxShadow: '0 1px 3px 0 rgba(58, 48, 20, 0.05)',
        height: '100%',
        transition: 'box-shadow 150ms ease, transform 150ms ease',
        ...(onClick && {
          cursor: 'pointer',
          '&:hover': {
            boxShadow: '0 6px 16px -4px rgba(58, 48, 20, 0.14)',
            transform: 'translateY(-1px)',
          },
        }),
      }}
    >
      <Box sx={{ p: { xs: 2, sm: 2.5 }, display: 'flex', flexDirection: 'column', gap: 1 }}>
        {icon && (
          <Box
            sx={{
              width: 42,
              height: 42,
              borderRadius: '12px',
              backgroundColor: styles.tileBg,
              color: tileColor,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {icon}
          </Box>
        )}
        {loading ? (
          <>
            <Skeleton width="60%" height={16} />
            <Skeleton width="80%" height={30} />
          </>
        ) : (
          <>
            <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 500 }}>
              {label}
            </Typography>
            <Typography
              variant="h5"
              sx={{ fontWeight: 700, color: valueColor, fontSize: '1.35rem' }}
            >
              {value}
            </Typography>
          </>
        )}
        {sublabel && !loading && (
          <Typography variant="caption" sx={{ color: 'text.disabled' }}>
            {sublabel}
          </Typography>
        )}
      </Box>
    </Card>
  );
};

export default StatCard;
