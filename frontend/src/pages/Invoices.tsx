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
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import AddCardIcon from '@mui/icons-material/AddCard';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatCurrency, formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { CreateInvoiceDialog } from '../components/CreateInvoiceDialog';
import { useCreateInvoice, useInvoiceList } from '../hooks/useInvoices';
import { INVOICE_STATUSES, INVOICE_STATUS_LABELS } from '../types/billing';
import type { InvoiceCreatePayload, InvoiceStatus } from '../types/billing';
import { PageHeader } from '../components/ui/PageHeader';
import { FilterBar } from '../components/ui/FilterBar';
import { TableCard } from '../components/ui/TableCard';
import { TableStateRow } from '../components/ui/TableStateRow';
import { AppPagination } from '../components/ui/AppPagination';
import { StatusBadge } from '../components/ui/StatusBadge';
import type { StatusTone } from '../components/ui/StatusBadge';

const PAGE_SIZE = 6;

const STATUS_TONES: Record<InvoiceStatus, StatusTone> = {
  UNPAID: 'error',
  PARTIALLY_PAID: 'warning',
  PAID: 'success',
};

export const Invoices: React.FC = () => {
  const navigate = useNavigate();
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<InvoiceStatus | ''>('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    setPage(1);
  }, [search, statusFilter, dateFrom, dateTo]);

  const { data, isLoading, isError, error, isFetching, refetch } = useInvoiceList({
    search: search || undefined,
    status: statusFilter || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    page,
  });

  const createMutation = useCreateInvoice();

  const handleCreate = (payload: InvoiceCreatePayload) => createMutation.mutateAsync(payload);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <PageHeader
        title="Invoices"
        subtitle="Track customer bills and payments."
        icon={<ReceiptLongIcon />}
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Invoices' }]}
        actions={
          isStaff && (
            <Button variant="contained" startIcon={<AddCardIcon />} onClick={() => setDialogOpen(true)}>
              Create Invoice
            </Button>
          )
        }
      />

      <FilterBar>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} flexWrap="wrap">
          <TextField
            label="Search"
            placeholder="Invoice no, order no, customer"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            size="small"
            sx={{ minWidth: 220 }}
          />
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              label="Status"
              onChange={(event) => setStatusFilter(event.target.value as InvoiceStatus | '')}
            >
              <MenuItem value="">All statuses</MenuItem>
              {INVOICE_STATUSES.map((status) => (
                <MenuItem key={status} value={status}>
                  {INVOICE_STATUS_LABELS[status]}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
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
        </Stack>
      </FilterBar>

      <TableCard loading={isFetching && !isLoading}>
        <Table size="medium">
          <TableHead>
            <TableRow>
              <TableCell>Invoice</TableCell>
              <TableCell>Customer</TableCell>
              <TableCell>Order</TableCell>
              <TableCell>Date</TableCell>
              <TableCell>Total</TableCell>
              <TableCell>Paid</TableCell>
              <TableCell>Balance Due</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableStateRow colSpan={8} state="loading" />
            ) : isError ? (
              <TableStateRow
                colSpan={8}
                state="error"
                errorMessage={getApiErrorMessage(error)}
                onRetry={() => refetch()}
              />
            ) : data && data.results.length === 0 ? (
              <TableStateRow colSpan={8} state="empty" emptyTitle="No invoices found" />
            ) : (
              data?.results.map((invoice) => (
                <TableRow
                  key={invoice.id}
                  hover
                  sx={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/invoices/${invoice.id}`)}
                >
                  <TableCell>
                    <Typography sx={{ fontWeight: 600 }}>{invoice.invoice_number}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{invoice.customer.full_name}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{invoice.order.order_number}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{formatDate(invoice.invoice_date)}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {formatCurrency(invoice.total_amount)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{formatCurrency(invoice.amount_paid)}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography
                      variant="body2"
                      sx={{
                        fontWeight: 600,
                        color: invoice.balance_due > 0 ? '#8F4A00' : '#1F5C3C',
                      }}
                    >
                      {formatCurrency(invoice.balance_due)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <StatusBadge label={INVOICE_STATUS_LABELS[invoice.status]} tone={STATUS_TONES[invoice.status]} />
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

      <CreateInvoiceDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        submit={handleCreate}
      />
    </Box>
  );
};

export default Invoices;
