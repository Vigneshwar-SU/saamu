import React from 'react';
import { Alert, Button, CircularProgress, TableCell, TableRow, Typography } from '@mui/material';

type TableState = 'loading' | 'error' | 'empty';

interface TableStateRowProps {
  colSpan: number;
  state: TableState;
  errorMessage?: string;
  emptyTitle?: string;
  emptyMessage?: string;
  emptyAction?: React.ReactNode;
  onRetry?: () => void;
}

export const TableStateRow: React.FC<TableStateRowProps> = ({
  colSpan,
  state,
  errorMessage,
  emptyTitle = 'No records found',
  emptyMessage,
  emptyAction,
  onRetry,
}) => {
  if (state === 'loading') {
    return (
      <TableRow>
        <TableCell colSpan={colSpan} align="center" sx={{ py: 8 }}>
          <CircularProgress size={30} />
        </TableCell>
      </TableRow>
    );
  }

  if (state === 'error') {
    return (
      <TableRow>
        <TableCell colSpan={colSpan} align="center" sx={{ py: 6 }}>
          <Alert severity="error" sx={{ display: 'inline-flex', textAlign: 'left' }}>
            {errorMessage ?? 'Something went wrong while loading data.'}
          </Alert>
          {onRetry && (
            <Button size="small" variant="outlined" onClick={onRetry} sx={{ mt: 1.5 }}>
              Retry
            </Button>
          )}
        </TableCell>
      </TableRow>
    );
  }

  return (
    <TableRow>
      <TableCell colSpan={colSpan} align="center" sx={{ py: 7 }}>
        <Typography sx={{ fontWeight: 600 }}>{emptyTitle}</Typography>
        {emptyMessage && (
          <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5 }}>
            {emptyMessage}
          </Typography>
        )}
        {emptyAction && <Typography sx={{ mt: 1.5 }}>{emptyAction}</Typography>}
      </TableCell>
    </TableRow>
  );
};

export default TableStateRow;
