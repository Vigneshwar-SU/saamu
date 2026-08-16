import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  Link,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import PaymentIcon from '@mui/icons-material/Payment';
import AddCardIcon from '@mui/icons-material/AddCard';
import CurrencyExchangeIcon from '@mui/icons-material/CurrencyExchange';
import { Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatCurrency, formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { useIncomeList, useIncomeSummary } from '../hooks/useFinance';
import { useCreatePayment, useInvoicePayments } from '../hooks/useInvoices';
import { RecordCustomerPaymentDialog } from '../components/RecordCustomerPaymentDialog';
import { SelectInvoiceForPaymentDialog } from '../components/SelectInvoiceForPaymentDialog';
import type { PaymentRecordMode } from '../components/SelectInvoiceForPaymentDialog';
import {
  PAYMENT_METHODS,
  PAYMENT_METHOD_LABELS,
  PAYMENT_TYPES,
  PAYMENT_TYPE_LABELS,
} from '../types/billing';
import type { CustomerPaymentPayload, Invoice, PaymentMethod, PaymentType } from '../types/billing';
import { PageHeader } from '../components/ui/PageHeader';
import { FilterBar } from '../components/ui/FilterBar';
import { ResponsiveTable } from '../components/ui/ResponsiveTable';
import { AppPagination } from '../components/ui/AppPagination';
import { StatCard } from '../components/ui/StatCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import type { StatusTone } from '../components/ui/StatusBadge';

const PAGE_SIZE = 6;

const PAYMENT_TYPE_TONES: Record<PaymentType, StatusTone> = {
  ADVANCE: 'info',
  PARTIAL: 'warning',
  FINAL: 'success',
  REFUND: 'error',
};

export const Payments: React.FC = () => {
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [paymentMethodFilter, setPaymentMethodFilter] = useState<PaymentMethod | ''>('');
  const [paymentTypeFilter, setPaymentTypeFilter] = useState<PaymentType | ''>('');
  const [page, setPage] = useState(1);

  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickerMode, setPickerMode] = useState<PaymentRecordMode>('PAYMENT');
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [recordDialogOpen, setRecordDialogOpen] = useState(false);

  useEffect(() => {
    setPage(1);
  }, [dateFrom, dateTo, paymentMethodFilter, paymentTypeFilter]);

  const filterParams = {
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    payment_method: paymentMethodFilter || undefined,
    payment_type: paymentTypeFilter || undefined,
  };

  const { data, isLoading, isError, error, isFetching, refetch } = useIncomeList({
    ...filterParams,
    page,
  });

  const summaryQuery = useIncomeSummary(filterParams);
  const summary = summaryQuery.data;

  const createPaymentMutation = useCreatePayment(selectedInvoice?.id ?? 0);
  const { data: selectedPaymentsData } = useInvoicePayments(selectedInvoice?.id ?? 0);
  const selectedPayments = selectedPaymentsData?.results ?? [];

  const handleRecordPayment = async (payload: CustomerPaymentPayload) => {
    await createPaymentMutation.mutateAsync(payload);
  };

  const openPicker = (mode: PaymentRecordMode) => {
    setPickerMode(mode);
    setSelectedInvoice(null);
    setRecordDialogOpen(false);
    setPickerOpen(true);
  };

  const handleInvoiceSelected = (invoice: Invoice) => {
    setSelectedInvoice(invoice);
    setPickerOpen(false);
    setRecordDialogOpen(true);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <PageHeader
        title="Payments"
        subtitle="Track advances, partial, final payments and refunds across all customers."
        icon={<PaymentIcon />}
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Payments' }]}
        actions={
          isStaff && (
            <>
              <Button
                variant="outlined"
                color="error"
                startIcon={<CurrencyExchangeIcon />}
                onClick={() => openPicker('REFUND')}
              >
                Record Refund
              </Button>
              <Button
                variant="contained"
                startIcon={<AddCardIcon />}
                onClick={() => openPicker('PAYMENT')}
              >
                Record Payment
              </Button>
            </>
          )
        }
      />

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' },
        }}
      >
        <StatCard
          label="Total Received"
          value={formatCurrency(summary?.total_income ?? 0)}
          sublabel="Net customer receipts in the selected range"
          tone="success"
        />
        <StatCard
          label="Payments"
          value={String(summary?.payment_count ?? 0)}
          sublabel="Payments in the selected range"
          tone="gold"
        />
        <StatCard
          label="Refunds"
          value={formatCurrency(summary?.total_refunds ?? 0)}
          sublabel={`${summary?.refund_count ?? 0} refund(s) in the selected range`}
          tone="error"
        />
      </Box>

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
            <InputLabel>Payment Type</InputLabel>
            <Select
              value={paymentTypeFilter}
              label="Payment Type"
              onChange={(event) => setPaymentTypeFilter(event.target.value as PaymentType | '')}
            >
              <MenuItem value="">All types</MenuItem>
              {PAYMENT_TYPES.map((type) => (
                <MenuItem key={type} value={type}>
                  {PAYMENT_TYPE_LABELS[type]}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel>Payment Method</InputLabel>
            <Select
              value={paymentMethodFilter}
              label="Payment Method"
              onChange={(event) => setPaymentMethodFilter(event.target.value as PaymentMethod | '')}
            >
              <MenuItem value="">All methods</MenuItem>
              {PAYMENT_METHODS.map((method) => (
                <MenuItem key={method} value={method}>
                  {PAYMENT_METHOD_LABELS[method]}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
      </FilterBar>

      <ResponsiveTable
        data={data?.results ?? []}
        rowKey={(payment) => payment.id}
        loading={isLoading}
        refetching={isFetching && !isLoading}
        error={isError}
        errorMessage={getApiErrorMessage(error)}
        onRetry={() => refetch()}
        emptyTitle="No payments found"
        emptyMessage="Record a payment against an invoice to get started."
        columns={[
          {
            label: 'Date',
            render: (payment) => (
              <Typography variant="body2">{formatDate(payment.payment_date)}</Typography>
            ),
          },
          {
            label: 'Type',
            render: (payment) => (
              <StatusBadge
                label={PAYMENT_TYPE_LABELS[payment.payment_type]}
                tone={PAYMENT_TYPE_TONES[payment.payment_type]}
              />
            ),
          },
          {
            label: 'Amount',
            render: (payment) => (
              <Typography
                variant="body2"
                sx={{
                  fontWeight: 600,
                  color: payment.payment_type === 'REFUND' ? '#8F2F22' : '#242424',
                }}
              >
                {payment.payment_type === 'REFUND' ? '− ' : ''}
                {formatCurrency(payment.net_amount)}
              </Typography>
            ),
          },
          {
            label: 'Method',
            render: (payment) => (
              <Typography variant="body2">{payment.payment_method_display}</Typography>
            ),
          },
          {
            label: 'Customer',
            primary: true,
            render: (payment) => (
              <Link
                component={RouterLink}
                to={`/customers/${payment.customer_id}`}
                underline="hover"
                color="inherit"
                sx={{ fontWeight: 500, fontSize: '0.875rem' }}
                onClick={(event) => event.stopPropagation()}
              >
                {payment.customer_name}
              </Link>
            ),
          },
          {
            label: 'Invoice',
            render: (payment) => (
              <Link
                component={RouterLink}
                to={`/invoices/${payment.invoice_id}`}
                underline="hover"
                color="inherit"
                sx={{ fontWeight: 600, fontSize: '0.875rem' }}
                onClick={(event) => event.stopPropagation()}
              >
                {payment.invoice_number}
              </Link>
            ),
          },
          {
            label: 'Recorded By',
            render: (payment) => (
              <Typography variant="body2">{payment.recorded_by_name || '-'}</Typography>
            ),
          },
        ]}
      />

      {data && data.count > 0 && (
        <AppPagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />
      )}

      <SelectInvoiceForPaymentDialog
        open={pickerOpen}
        mode={pickerMode}
        onClose={() => setPickerOpen(false)}
        onSelect={handleInvoiceSelected}
      />

      {selectedInvoice && (
        <RecordCustomerPaymentDialog
          open={recordDialogOpen}
          onClose={() => setRecordDialogOpen(false)}
          submit={handleRecordPayment}
          invoice={selectedInvoice}
          refundMode={pickerMode === 'REFUND'}
          payments={selectedPayments}
        />
      )}
    </Box>
  );
};

export default Payments;
