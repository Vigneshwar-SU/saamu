import React from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CircularProgress,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
  useMediaQuery,
} from '@mui/material';
import type { Theme } from '@mui/material';
import { TableCard } from './TableCard';
import { TableStateRow } from './TableStateRow';

export interface ResponsiveColumn<T> {
  label: string;
  render: (row: T) => React.ReactNode;
  align?: 'left' | 'right' | 'center';
  /** Marks the cell as the prominent title on the mobile card. */
  primary?: boolean;
  /** Hide this column on mobile cards only (desktop table unaffected). */
  hideOnMobile?: boolean;
}

interface ResponsiveTableProps<T> {
  data: T[];
  columns: Array<ResponsiveColumn<T>>;
  rowKey: (row: T) => string | number;
  onRowClick?: (row: T) => void;
  actions?: (row: T) => React.ReactNode;
  size?: 'small' | 'medium';
  loading?: boolean;
  refetching?: boolean;
  error?: boolean;
  errorMessage?: string;
  onRetry?: () => void;
  emptyTitle?: string;
  emptyMessage?: string;
  emptyAction?: React.ReactNode;
}

export const ResponsiveTable = <T,>({
  data,
  columns,
  rowKey,
  onRowClick,
  actions,
  size = 'medium',
  loading = false,
  refetching = false,
  error = false,
  errorMessage,
  onRetry,
  emptyTitle,
  emptyMessage,
  emptyAction,
}: ResponsiveTableProps<T>) => {
  const isDesktop = useMediaQuery((theme: Theme) => theme.breakpoints.up('sm'), { noSsr: true });
  const colSpan = columns.length + (actions ? 1 : 0);

  if (loading) {
    return isDesktop ? (
      <TableCard loading={refetching}>
        <Table size={size}>
          <TableBody>
            <TableStateRow colSpan={colSpan} state="loading" />
          </TableBody>
        </Table>
      </TableCard>
    ) : (
      <Card
        sx={{
          borderRadius: '12px',
          border: '1px solid #E7E0D0',
          boxShadow: '0 1px 3px 0 rgba(58, 48, 20, 0.05)',
          py: 6,
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <CircularProgress size={30} />
      </Card>
    );
  }

  if (error) {
    return isDesktop ? (
      <TableCard loading={refetching}>
        <Table size={size}>
          <TableBody>
            <TableStateRow
              colSpan={colSpan}
              state="error"
              errorMessage={errorMessage}
              onRetry={onRetry}
            />
          </TableBody>
        </Table>
      </TableCard>
    ) : (
      <Card
        sx={{
          borderRadius: '12px',
          border: '1px solid #E7E0D0',
          boxShadow: '0 1px 3px 0 rgba(58, 48, 20, 0.05)',
          p: 3,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 1.5,
          textAlign: 'center',
        }}
      >
        <Alert severity="error" sx={{ textAlign: 'left' }}>
          {errorMessage ?? 'Something went wrong while loading data.'}
        </Alert>
        {onRetry && (
          <Button size="small" variant="outlined" onClick={onRetry}>
            Retry
          </Button>
        )}
      </Card>
    );
  }

  if (data.length === 0) {
    return isDesktop ? (
      <TableCard loading={refetching}>
        <Table size={size}>
          <TableBody>
            <TableStateRow
              colSpan={colSpan}
              state="empty"
              emptyTitle={emptyTitle}
              emptyMessage={emptyMessage}
              emptyAction={emptyAction}
            />
          </TableBody>
        </Table>
      </TableCard>
    ) : (
      <Card
        sx={{
          borderRadius: '12px',
          border: '1px solid #E7E0D0',
          boxShadow: '0 1px 3px 0 rgba(58, 48, 20, 0.05)',
          p: 4,
          textAlign: 'center',
        }}
      >
        <Typography sx={{ fontWeight: 600 }}>{emptyTitle ?? 'No records found'}</Typography>
        {emptyMessage && (
          <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5 }}>
            {emptyMessage}
          </Typography>
        )}
        {emptyAction && <Box sx={{ mt: 1.5 }}>{emptyAction}</Box>}
      </Card>
    );
  }

  if (!isDesktop) {
    return (
      <Stack spacing={2}>
        {data.map((row) => {
          const key = rowKey(row);
          const visibleColumns = columns.filter((column) => !column.hideOnMobile);
          const primaryColumn = columns.find((column) => column.primary);
          const hasRowClick = Boolean(onRowClick);

          return (
            <Card
              key={key}
              role={hasRowClick ? 'button' : undefined}
              tabIndex={hasRowClick ? 0 : undefined}
              onClick={hasRowClick ? () => onRowClick!(row) : undefined}
              onKeyDown={
                hasRowClick
                  ? (event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        onRowClick!(row);
                      }
                    }
                  : undefined
              }
              sx={{
                borderRadius: '12px',
                border: '1px solid #E7E0D0',
                boxShadow: '0 1px 3px 0 rgba(58, 48, 20, 0.05)',
                p: 2,
                display: 'flex',
                flexDirection: 'column',
                gap: 1.5,
                ...(hasRowClick && {
                  cursor: 'pointer',
                  outline: 'none',
                  '&:hover': {
                    borderColor: '#D6CBAA',
                    boxShadow: '0 4px 12px -2px rgba(58, 48, 20, 0.10)',
                  },
                  '&:focus-visible': { borderColor: '#8F6E10' },
                }),
              }}
            >
              {primaryColumn && <Box>{primaryColumn.render(row)}</Box>}
              <Stack spacing={1.25}>
                {visibleColumns
                  .filter((column) => !column.primary)
                  .map((column) => (
                    <Box
                      key={column.label}
                      sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'baseline',
                        gap: 2,
                      }}
                    >
                      <Typography
                        variant="caption"
                        sx={{ color: 'text.secondary', fontWeight: 600, flexShrink: 0 }}
                      >
                        {column.label}
                      </Typography>
                      <Box sx={{ textAlign: 'right', minWidth: 0 }}>{column.render(row)}</Box>
                    </Box>
                  ))}
              </Stack>
              {actions && (
                <Box
                  sx={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 1,
                    pt: 1,
                    borderTop: '1px solid #F0EADA',
                  }}
                >
                  {actions(row)}
                </Box>
              )}
            </Card>
          );
        })}
      </Stack>
    );
  }

  return (
    <TableCard loading={refetching}>
      <Table size={size}>
        <TableHead>
          <TableRow>
            {columns.map((column) => (
              <TableCell key={column.label} align={column.align}>
                {column.label}
              </TableCell>
            ))}
            {actions && <TableCell align="right" />}
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((row) => (
            <TableRow
              key={rowKey(row)}
              hover
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              sx={{
                ...(onRowClick && { cursor: 'pointer' }),
                '&:last-child td, &:last-child th': { border: 0 },
              }}
            >
              {columns.map((column) => (
                <TableCell key={column.label} align={column.align}>
                  {column.render(row)}
                </TableCell>
              ))}
              {actions && (
                <TableCell align="right">
                  <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                    {actions(row)}
                  </Box>
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableCard>
  );
};

export default ResponsiveTable;
