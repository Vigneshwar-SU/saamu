import React from 'react';
import { Box, Typography, Container, Stack, Tooltip, CircularProgress } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import { useHealth } from '../hooks/useHealth';

export const Footer: React.FC = () => {
  const { data: health, isLoading, isError } = useHealth();
  const currentYear = new Date().getFullYear();

  return (
    <Box
      component="footer"
      sx={{
        py: 2,
        px: 3,
        mt: 'auto',
        backgroundColor: '#FFFFFF',
        borderTop: '1px solid #E2E8F0',
      }}
    >
      <Container maxWidth={false}>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          justifyContent="space-between"
          alignItems="center"
          spacing={1}
        >
          <Typography variant="body2" sx={{ color: '#64748B', fontSize: '0.85rem' }}>
            © {currentYear} <strong>Saamu Tailors</strong>. Enterprise Tailoring Management System. All rights reserved.
          </Typography>

          <Stack direction="row" spacing={2} alignItems="center">
            {/* System Health Check Indicator */}
            <Tooltip
              title={
                health
                  ? `Backend connected: ${health.application} v${health.version}`
                  : isError
                  ? 'Backend unreachable or PostgreSQL offline'
                  : 'Checking backend status...'
              }
            >
              <Stack direction="row" spacing={0.75} alignItems="center">
                {isLoading ? (
                  <CircularProgress size={12} color="inherit" />
                ) : health?.status === 'ok' ? (
                  <CheckCircleIcon sx={{ fontSize: 16, color: '#22C55E' }} />
                ) : (
                  <ErrorOutlineIcon sx={{ fontSize: 16, color: '#EF4444' }} />
                )}
                <Typography
                  variant="caption"
                  sx={{
                    fontWeight: 600,
                    color: health?.status === 'ok' ? '#15803D' : isError ? '#B91C1C' : '#64748B',
                    fontSize: '0.75rem',
                  }}
                >
                  {isLoading
                    ? 'Connecting API...'
                    : health?.status === 'ok'
                    ? 'Backend API: Online'
                    : 'Backend API: Offline'}
                </Typography>
              </Stack>
            </Tooltip>
          </Stack>
        </Stack>
      </Container>
    </Box>
  );
};
