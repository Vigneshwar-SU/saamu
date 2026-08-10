import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  InputLabel,
  LinearProgress,
  Link,
  MenuItem,
  Pagination,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
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
import type {
  CustomerPaymentPayload,
  Invoice,
  PaymentMethod,
  PaymentType,
} from '../types/billing';

const PAGE_SIZE = 20;

const PAYMENT_TYPE_COLORS: Record<PaymentType, { bg: string; text: string }> = {
  ADVANCE: { bg: '#E0E7FF', text: '#4338CA' },
  PARTIAL: { bg: '#DBEAFE', text: '#1D4ED8' },
  FINAL: { bg: '#DCFCE7', text: '#15803D' },
  REFUND: { bg: '#FEE2E2', text: '#B91C1C' },
};

interface StatCardProps {
  label: string;
  value: string;
  sublabel?: string;
  accent: string;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, sublabel, accent }) => {
  return (
    <Card sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', boxShadow: 'none' }}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
        <Typography variant="body2" sx={{ color: '#64748B', fontWeight: 500 }}>
          {label}
        </Typography>
        <Typography variant="h5" sx={{ fontWeight: 700, color: accent }}>
          {value}
        </Typography>
        {sublabel && (
          <Typography variant="caption" sx={{ color: '#94A3B8' }}>
            {sublabel}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
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

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

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
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
        <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
          Saamu Tailors ERP
        </Link>
        <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
          Payments
        </Typography>
      </Breadcrumbs>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: '12px',
              backgroundColor: '#EFF6FF',
              color: '#1E3A8A',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <PaymentIcon />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              Payments
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              Track advances, partial, final payments and refunds across all customers.
            </Typography>
          </Box>
        </Box>
        {isStaff && (
          <Stack direction="row" spacing={1.5} flexWrap="wrap">
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
              sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
            >
              Record Payment
            </Button>
          </Stack>
        )}
      </Box>

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
          accent="#15803D"
        />
        <StatCard
          label="Payments"
          value={String(summary?.payment_count ?? 0)}
          sublabel="Payments in the selected range"
          accent="#1E3A8A"
        />
        <StatCard
          label="Refunds"
          value={formatCurrency(summary?.total_refunds ?? 0)}
          sublabel={`${summary?.refund_count ?? 0} refund(s) in the selected range`}
          accent="#B91C1C"
        />
      </Box>

      <Paper sx={{ p: 2, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
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
              onChange={(event) =>
                setPaymentMethodFilter(event.target.value as PaymentMethod | '')
              }
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
      </Paper>

      <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        {isFetching && !isLoading && <LinearProgress sx={{ height: 3 }} />}
        <TableContainer>
          <Table size="medium">
            <TableHead>
              <TableRow sx={{ backgroundColor: '#F8FAFC' }}>
                <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Type</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Amount</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Method</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Customer</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Invoice</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Recorded By</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 6 }}>
                    <CircularProgress size={28} />
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <Alert severity="error" sx={{ display: 'inline-flex' }}>
                      {getApiErrorMessage(error)}
                    </Alert>
                    <Box sx={{ mt: 1.5 }}>
                      <Button size="small" variant="outlined" onClick={() => refetch()}>
                        Retry
                      </Button>
                    </Box>
                  </TableCell>
                </TableRow>
              ) : data && data.results.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 6 }}>
                    <Typography sx={{ color: '#64748B' }}>
                      No payments found. Record a payment against an invoice to get started.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                data?.results.map((payment) => {
                  const isRefund = payment.payment_type === 'REFUND';
                  const typeColors = PAYMENT_TYPE_COLORS[payment.payment_type];
                  return (
                    <TableRow
                      key={payment.id}
                      hover
                      sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                    >
                      <TableCell>
                        <Typography variant="body2">{formatDate(payment.payment_date)}</Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={PAYMENT_TYPE_LABELS[payment.payment_type]}
                          size="small"
                          sx={{
                            fontWeight: 600,
                            backgroundColor: typeColors.bg,
                            color: typeColors.text,
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          sx={{ fontWeight: 600, color: isRefund ? '#B91C1C' : '#0F172A' }}
                        >
                          {isRefund ? '− ' : ''}
                          {formatCurrency(payment.net_amount)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{payment.payment_method_display}</Typography>
                      </TableCell>
                      <TableCell>
                        <Link
                          component={RouterLink}
                          to={`/customers/${payment.customer_id}`}
                          underline="hover"
                          color="inherit"
                          sx={{ fontWeight: 500, fontSize: '0.875rem' }}
                        >
                          {payment.customer_name}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Link
                          component={RouterLink}
                          to={`/invoices/${payment.invoice_id}`}
                          underline="hover"
                          color="inherit"
                          sx={{ fontWeight: 600, fontSize: '0.875rem' }}
                        >
                          {payment.invoice_number}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{payment.recorded_by_name || '-'}</Typography>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {data && data.count > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" sx={{ color: '#64748B' }}>
            Showing {data.results.length} of {data.count} payments
          </Typography>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(_event, value) => setPage(value)}
            color="primary"
          />
        </Box>
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
