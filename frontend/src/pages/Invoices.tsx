import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
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
import { ResponsiveTable } from '../components/ui/ResponsiveTable';
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
            <Button
              variant="contained"
              startIcon={<AddCardIcon />}
              onClick={() => setDialogOpen(true)}
            >
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

      <ResponsiveTable
        data={data?.results ?? []}
        rowKey={(invoice) => invoice.id}
        onRowClick={(invoice) => navigate(`/invoices/${invoice.id}`)}
        loading={isLoading}
        refetching={isFetching && !isLoading}
        error={isError}
        errorMessage={getApiErrorMessage(error)}
        onRetry={() => refetch()}
        emptyTitle="No invoices found"
        columns={[
          {
            label: 'Invoice',
            primary: true,
            render: (invoice) => (
              <Typography sx={{ fontWeight: 600 }}>{invoice.invoice_number}</Typography>
            ),
          },
          {
            label: 'Customer',
            render: (invoice) => (
              <Typography variant="body2">{invoice.customer.full_name}</Typography>
            ),
          },
          {
            label: 'Order',
            render: (invoice) => (
              <Typography variant="body2">{invoice.order.order_number}</Typography>
            ),
          },
          {
            label: 'Date',
            render: (invoice) => (
              <Typography variant="body2">{formatDate(invoice.invoice_date)}</Typography>
            ),
          },
          {
            label: 'Total',
            render: (invoice) => (
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {formatCurrency(invoice.total_amount)}
              </Typography>
            ),
          },
          {
            label: 'Paid',
            render: (invoice) => (
              <Typography variant="body2">{formatCurrency(invoice.amount_paid)}</Typography>
            ),
          },
          {
            label: 'Balance Due',
            render: (invoice) => (
              <Typography
                variant="body2"
                sx={{
                  fontWeight: 600,
                  color: invoice.balance_due > 0 ? '#8F4A00' : '#1F5C3C',
                }}
              >
                {formatCurrency(invoice.balance_due)}
              </Typography>
            ),
          },
          {
            label: 'Status',
            render: (invoice) => (
              <StatusBadge
                label={INVOICE_STATUS_LABELS[invoice.status]}
                tone={STATUS_TONES[invoice.status]}
              />
            ),
          },
        ]}
      />

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
