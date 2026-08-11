import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import AddCardIcon from '@mui/icons-material/AddCard';
import { useAuth } from '../context/useAuth';
import { formatCurrency, formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { AddAdvanceDialog } from '../components/AddAdvanceDialog';
import { useAdvanceList, useCreateAdvance } from '../hooks/useAdvances';
import { useTailorList } from '../hooks/useTailors';
import {
  ADVANCE_STATUS_LABELS,
  ADVANCE_STATUSES,
} from '../types/advances';
import type { AdvancePayload, AdvanceStatus } from '../types/advances';
import { PageHeader } from '../components/ui/PageHeader';
import { FilterBar } from '../components/ui/FilterBar';
import { TableCard } from '../components/ui/TableCard';
import { TableStateRow } from '../components/ui/TableStateRow';
import { AppPagination } from '../components/ui/AppPagination';
import { StatusBadge } from '../components/ui/StatusBadge';

const PAGE_SIZE = 6;

export const Advances: React.FC = () => {
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [tailorFilter, setTailorFilter] = useState<number | ''>('');
  const [statusFilter, setStatusFilter] = useState<AdvanceStatus | ''>('');
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data: tailorsData } = useTailorList({ scope: 'all', page_size: 100 });
  const tailors = tailorsData?.results ?? [];

  useEffect(() => {
    setPage(1);
  }, [dateFrom, dateTo, tailorFilter, statusFilter]);

  const { data, isLoading, isError, error, isFetching, refetch } = useAdvanceList({
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    tailor: tailorFilter === '' ? undefined : tailorFilter,
    status: statusFilter || undefined,
    page,
  });

  const createMutation = useCreateAdvance();

  const handleCreate = (payload: AdvancePayload) => createMutation.mutateAsync(payload);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <PageHeader
        title="Advances"
        subtitle="Track tailor salary advances and deductions."
        icon={<AccountBalanceWalletIcon />}
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Advances' }]}
        actions={
          isStaff && (
            <Button variant="contained" startIcon={<AddCardIcon />} onClick={() => setDialogOpen(true)}>
              Add Advance
            </Button>
          )
        }
      />

      <FilterBar>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} flexWrap="wrap">
          <TextField
            label="From"
            type="date"
            value={dateFrom}
            onChange={(event) => setDateFrom(event.target.value)}
            size="small"
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="To"
            type="date"
            value={dateTo}
            onChange={(event) => setDateTo(event.target.value)}
            size="small"
            InputLabelProps={{ shrink: true }}
          />
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel>Tailor</InputLabel>
            <Select
              value={tailorFilter}
              label="Tailor"
              onChange={(event) => setTailorFilter(event.target.value as number | '')}
            >
              <MenuItem value="">All tailors</MenuItem>
              {tailors.map((tailor) => (
                <MenuItem key={tailor.id} value={tailor.id}>
                  {tailor.name}
                  {tailor.is_active ? '' : ' (Archived)'}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              label="Status"
              onChange={(event) => setStatusFilter(event.target.value as AdvanceStatus | '')}
            >
              <MenuItem value="">All statuses</MenuItem>
              {ADVANCE_STATUSES.map((status) => (
                <MenuItem key={status} value={status}>
                  {ADVANCE_STATUS_LABELS[status]}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
      </FilterBar>

      <TableCard loading={isFetching && !isLoading}>
        <Table size="medium">
          <TableHead>
            <TableRow>
              <TableCell>Tailor</TableCell>
              <TableCell>Amount</TableCell>
              <TableCell>Date</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Notes</TableCell>
              <TableCell>Recorded By</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableStateRow colSpan={6} state="loading" />
            ) : isError ? (
              <TableStateRow
                colSpan={6}
                state="error"
                errorMessage={getApiErrorMessage(error)}
                onRetry={() => refetch()}
              />
            ) : data && data.results.length === 0 ? (
              <TableStateRow colSpan={6} state="empty" emptyTitle="No advances found" />
            ) : (
              data?.results.map((advance) => (
                <TableRow key={advance.id} hover>
                  <TableCell>
                    <Typography sx={{ fontWeight: 600 }}>{advance.tailor.name}</Typography>
                    <Typography variant="caption" sx={{ color: 'text.disabled' }}>
                      #{advance.tailor.id}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {formatCurrency(advance.amount)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{formatDate(advance.advance_date)}</Typography>
                  </TableCell>
                  <TableCell>
                    <StatusBadge
                      label={ADVANCE_STATUS_LABELS[advance.status]}
                      tone={advance.status === 'OUTSTANDING' ? 'warning' : 'neutral'}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ maxWidth: 260 }}>
                      {advance.notes || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{advance.recorded_by_name || '-'}</Typography>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableCard>

      {data && data.count > 0 && (
        <AppPagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />
      )}

      <AddAdvanceDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        submit={handleCreate}
      />
    </Box>
  );
};

export default Advances;
