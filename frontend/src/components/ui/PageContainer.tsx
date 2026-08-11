import React from 'react';
import { Box } from '@mui/material';
import type { SxProps, Theme } from '@mui/material';

interface PageContainerProps {
  children: React.ReactNode;
  sx?: SxProps<Theme>;
  maxWidth?: number | string;
}

export const PageContainer: React.FC<PageContainerProps> = ({
  children,
  sx,
  maxWidth = 1400,
}) => {
  return (
    <Box
      sx={{
        width: '100%',
        maxWidth,
        mx: 'auto',
        ...sx,
      }}
    >
      {children}
    </Box>
  );
};

export default PageContainer;
