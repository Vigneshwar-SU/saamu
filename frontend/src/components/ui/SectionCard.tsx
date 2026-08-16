import React from 'react';
import { Box, Card, Typography } from '@mui/material';
import type { SxProps, Theme } from '@mui/material';

interface SectionCardProps {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  children: React.ReactNode;
  noPadding?: boolean;
  sx?: SxProps<Theme>;
}

export const SectionCard: React.FC<SectionCardProps> = ({
  title,
  subtitle,
  action,
  icon,
  children,
  noPadding = false,
  sx,
}) => {
  return (
    <Card
      sx={{
        borderRadius: '14px',
        border: '1px solid #E7E0D0',
        boxShadow: '0 1px 3px 0 rgba(58, 48, 20, 0.05)',
        overflow: 'hidden',
        ...sx,
      }}
    >
      {(title || action) && (
        <Box
          sx={{
            px: { xs: 2, sm: 2.5 },
            py: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 2,
            flexWrap: 'wrap',
            borderBottom: '1px solid #E7E0D0',
            backgroundColor: '#FBF6EA',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, minWidth: 0 }}>
            {icon && (
              <Box
                sx={{
                  width: 34,
                  height: 34,
                  borderRadius: '10px',
                  backgroundColor: '#F5EBD2',
                  color: '#A98216',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {icon}
              </Box>
            )}
            <Box sx={{ minWidth: 0 }}>
              {title && (
                <Typography sx={{ fontWeight: 700, fontSize: '1rem', lineHeight: 1.3 }}>
                  {title}
                </Typography>
              )}
              {subtitle && (
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  {subtitle}
                </Typography>
              )}
            </Box>
          </Box>
          {action && <Box sx={{ flexShrink: 0 }}>{action}</Box>}
        </Box>
      )}
      <Box sx={noPadding ? undefined : { p: { xs: 2, sm: 2.5 } }}>{children}</Box>
    </Card>
  );
};

export default SectionCard;
