import React from 'react';
import { Box, Skeleton, Typography } from '@mui/material';

interface InfoFieldProps {
  label: string;
  value?: React.ReactNode;
  loading?: boolean;
  strong?: boolean;
}

export const InfoField: React.FC<InfoFieldProps> = ({
  label,
  value,
  loading = false,
  strong = false,
}) => {
  return (
    <Box>
      <Typography
        variant="caption"
        sx={{ color: 'text.secondary', fontWeight: 600, display: 'block', mb: 0.5 }}
      >
        {label}
      </Typography>
      {loading ? (
        <Skeleton width={120} height={22} />
      ) : (
        <Typography variant="body2" sx={{ fontWeight: strong ? 700 : 500, color: 'text.primary' }}>
          {value ?? '—'}
        </Typography>
      )}
    </Box>
  );
};

export default InfoField;
