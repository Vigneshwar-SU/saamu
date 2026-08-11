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
        borderTop: '1px solid #E7E0D0',
      }}
    >
      <Container maxWidth={false}>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          justifyContent="space-between"
          alignItems="center"
          spacing={1}
        >
          <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: '0.85rem' }}>
            © {currentYear} <strong style={{ color: '#242424' }}>Saamu Tailors</strong>. Enterprise Tailoring
            Management System. All rights reserved.
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
                  <CheckCircleIcon sx={{ fontSize: 16, color: '#2E7D52' }} />
                ) : (
                  <ErrorOutlineIcon sx={{ fontSize: 16, color: '#B3402F' }} />
                )}
                <Typography
                  variant="caption"
                  sx={{
                    fontWeight: 600,
                    color: health?.status === 'ok' ? '#1F5C3C' : isError ? '#8F2F22' : 'text.secondary',
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

export default Footer;
