import React from 'react';
import { Alert, Box, Button, Paper, Stack, Typography } from '@mui/material';

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: unknown, errorInfo: React.ErrorInfo): void {
    console.error('Unhandled render error:', error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({ hasError: false });
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <Paper
          sx={{
            p: 4,
            maxWidth: 480,
            borderRadius: '12px',
            border: '1px solid #E2E8F0',
            boxShadow: 'none',
          }}
        >
          <Stack spacing={2} alignItems="center" textAlign="center">
            <Alert severity="error" sx={{ display: 'inline-flex' }}>
              Something went wrong while rendering this page.
            </Alert>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              The error has been logged. Try reloading the page or sign in again.
            </Typography>
            <Stack direction="row" spacing={1}>
              <Button variant="contained" onClick={() => window.location.reload()}>
                Reload
              </Button>
              <Button variant="outlined" onClick={this.handleReset}>
                Try again
              </Button>
            </Stack>
          </Stack>
        </Paper>
      </Box>
    );
  }
}

export default ErrorBoundary;
