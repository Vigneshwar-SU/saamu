import React from 'react';
import { Box, Typography } from '@mui/material';
import InboxIcon from '@mui/icons-material/Inbox';

interface EmptyStateProps {
  title: string;
  message?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ title, message, icon, action }) => {
  return (
    <Box sx={{ py: 6, px: 3, textAlign: 'center' }}>
      <Box
        sx={{
          width: 56,
          height: 56,
          mx: 'auto',
          borderRadius: '16px',
          backgroundColor: '#F5EBD2',
          color: '#A98216',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mb: 1.5,
        }}
      >
        {icon ?? <InboxIcon />}
      </Box>
      <Typography sx={{ fontWeight: 600 }}>{title}</Typography>
      {message && (
        <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5, maxWidth: 420, mx: 'auto' }}>
          {message}
        </Typography>
      )}
      {action && <Box sx={{ mt: 2 }}>{action}</Box>}
    </Box>
  );
};

export default EmptyState;
