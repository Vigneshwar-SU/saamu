import React from 'react';
import { Alert, Box, Button, Stack, Typography } from '@mui/material';
import CloudOffIcon from '@mui/icons-material/CloudOff';

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ message, onRetry }) => {
  return (
    <Box sx={{ py: 6, px: 3, textAlign: 'center' }}>
      <Box
        sx={{
          width: 56,
          height: 56,
          mx: 'auto',
          borderRadius: '16px',
          backgroundColor: '#FBE9E6',
          color: '#B3402F',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mb: 1.5,
        }}
      >
        <CloudOffIcon />
      </Box>
      <Typography sx={{ fontWeight: 600 }}>Something went wrong</Typography>
      {message && (
        <Alert severity="error" sx={{ mt: 1.5, justifyContent: 'center' }}>
          {message}
        </Alert>
      )}
      {onRetry && (
        <Stack direction="row" justifyContent="center" sx={{ mt: 2 }}>
          <Button variant="outlined" onClick={onRetry}>
            Retry
          </Button>
        </Stack>
      )}
    </Box>
  );
};

export default ErrorState;
