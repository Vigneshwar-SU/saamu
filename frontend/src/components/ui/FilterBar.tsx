import React from 'react';
import { Paper } from '@mui/material';
import type { SxProps, Theme } from '@mui/material';

interface FilterBarProps {
  children: React.ReactNode;
  sx?: SxProps<Theme>;
}

export const FilterBar: React.FC<FilterBarProps> = ({ children, sx }) => {
  return (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        borderRadius: '12px',
        border: '1px solid #E7E0D0',
        backgroundColor: '#FFFFFF',
        ...sx,
      }}
    >
      {children}
    </Paper>
  );
};

export default FilterBar;
