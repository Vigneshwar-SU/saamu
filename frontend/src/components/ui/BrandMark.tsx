import React from 'react';
import { Box } from '@mui/material';
import ContentCutIcon from '@mui/icons-material/ContentCut';

interface BrandMarkProps {
  size?: number;
}

export const BrandMark: React.FC<BrandMarkProps> = ({ size = 40 }) => {
  return (
    <Box
      sx={{
        width: size,
        height: size,
        flexShrink: 0,
        borderRadius: '12px',
        background: 'linear-gradient(135deg, #C9A227 0%, #A98216 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#FFFFFF',
        boxShadow: '0 2px 6px rgba(169, 130, 22, 0.35)',
      }}
    >
      <ContentCutIcon sx={{ fontSize: size * 0.55 }} />
    </Box>
  );
};

export default BrandMark;
