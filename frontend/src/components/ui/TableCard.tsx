import React from 'react';
import { LinearProgress, Paper, TableContainer } from '@mui/material';
import type { SxProps, Theme } from '@mui/material';

interface TableCardProps {
  children: React.ReactNode;
  loading?: boolean;
  sx?: SxProps<Theme>;
}

export const TableCard: React.FC<TableCardProps> = ({ children, loading = false, sx }) => {
  return (
    <Paper
      elevation={0}
      sx={{
        borderRadius: '12px',
        border: '1px solid #E7E0D0',
        overflow: 'hidden',
        backgroundColor: '#FFFFFF',
        ...sx,
      }}
    >
      {loading && <LinearProgress sx={{ height: 3 }} />}
      <TableContainer>{children}</TableContainer>
    </Paper>
  );
};

export default TableCard;
