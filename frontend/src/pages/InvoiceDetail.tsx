import React, { useState } from 'react';
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  CircularProgress,
  Link,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import PaymentsIcon from '@mui/icons-material/Payments';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatCurrency, formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { RecordCustomerPaymentDialog } from '../components/RecordCustomerPaymentDialog';
import { useCreatePayment, useInvoice, useInvoicePayments } from '../hooks/useInvoices';
import { INVOICE_STATUS_COLORS, INVOICE_STATUS_LABELS } from '../types/billing';
import type { CustomerPaymentPayload } from '../types/billing';

const SummaryCard: React.FC<{ label: string; value: string; color?: string }> = ({
  label,
  value,
  color,
}) => (
  <Paper sx={{ flex: 1, minWidth: 160, p: 2, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
    <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
      {label}
    </Typography>
    <Typography variant="h5" sx={{ fontWeight: 700, mt: 0.5, color: color ?? '#0F172A' }}>
      {value}
    </Typography>
  </Paper>
);

export const InvoiceDetail: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const invoiceId = Number(id ?? 0);
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [settleDialogOpen, setSettleDialogOpen] = useState(false);

  const { data: invoice, isLoading, isError, error, refetch } = useInvoice(invoiceId);
  const { data: paymentsData } = useInvoicePayments(invoiceId);

  const createPaymentMutation = useCreatePayment(invoiceId);

  const payments = paymentsData?.results ?? [];

  const handleRecordPayment = async (payload: CustomerPaymentPayload) => {
    await createPaymentMutation.mutateAsync(payload);
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress size={32} />
      </Box>
    );
  }

  if (isError || !invoice) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, alignItems: 'flex-start' }}>
        <Alert severity="error">{getApiErrorMessage(error)}</Alert>
        <Button size="small" variant="outlined" onClick={() => refetch()}>
          Retry
        </Button>
      </Box>
    );
  }

  const colors = INVOICE_STATUS_COLORS[invoice.status];
  const canRecord = isStaff && invoice.balance_due > 0;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
          <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
            Saamu Tailors ERP
          </Link>
          <Link underline="hover" color="inherit" href="/invoices" sx={{ fontSize: '0.85rem' }}>
            Invoices
          </Link>
          <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
            {invoice.invoice_number}
          </Typography>
        </Breadcrumbs>
        <Button size="small" startIcon={<ArrowBackIcon />} onClick={() => navigate('/invoices')}>
          Back to Invoices
        </Button>
      </Box>

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
            <ReceiptLongIcon />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              {invoice.invoice_number}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 0.5 }}>
              <Chip
                label={INVOICE_STATUS_LABELS[invoice.status]}
                size="small"
                sx={{ fontWeight: 600, backgroundColor: colors.bg, color: colors.text }}
              />
              <Typography variant="body2" sx={{ color: '#64748B' }}>
                {invoice.payment_count} payment{invoice.payment_count === 1 ? '' : 's'}
              </Typography>
            </Stack>
          </Box>
        </Box>
        {canRecord && (
          <Stack direction="row" spacing={1.5} flexWrap="wrap">
            <Button
              variant="outlined"
              startIcon={<PaymentsIcon />}
              onClick={() => setPaymentDialogOpen(true)}
            >
              Record Payment
            </Button>
            <Button
              variant="contained"
              startIcon={<VerifiedUserIcon />}
              onClick={() => setSettleDialogOpen(true)}
              sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
            >
              Settle in Full
            </Button>
          </Stack>
        )}
      </Box>

      <Paper sx={{ p: 2, borderRadius: '12px', border: '1px solid #E2E8F0', backgroundColor: '#F8FAFC' }}>
        <Stack spacing={1}>
          <Stack direction="row" spacing={4} flexWrap="wrap">
            <Box>
              <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
                CUSTOMER
              </Typography>
              <Typography sx={{ fontWeight: 600 }}>{invoice.customer.full_name}</Typography>
              <Typography variant="body2" sx={{ color: '#64748B' }}>
                {invoice.customer.mobile_number}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
                ORDER
              </Typography>
              <Link
                underline="hover"
                color="inherit"
                href={`/orders/${invoice.order.id}`}
                sx={{ fontWeight: 600, fontSize: '0.9rem' }}
              >
                {invoice.order.order_number}
              </Link>
              <Typography variant="body2" sx={{ color: '#64748B' }}>
                {formatDate(invoice.order.order_date)}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
                INVOICE DATE
              </Typography>
              <Typography sx={{ fontWeight: 600 }}>{formatDate(invoice.invoice_date)}</Typography>
            </Box>
            {invoice.created_by_name && (
              <Box>
                <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
                  CREATED BY
                </Typography>
                <Typography sx={{ fontWeight: 600 }}>{invoice.created_by_name}</Typography>
              </Box>
            )}
          </Stack>
          {invoice.notes && (
            <Typography
              variant="body2"
              sx={{ color: '#475569', whiteSpace: 'pre-wrap', mt: 1, pt: 1, borderTop: '1px solid #E2E8F0' }}
            >
              {invoice.notes}
            </Typography>
          )}
        </Stack>
      </Paper>

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} flexWrap="wrap">
        <SummaryCard label="SUBTOTAL" value={formatCurrency(invoice.subtotal)} />
        <SummaryCard label="ADJUSTMENT" value={formatCurrency(invoice.adjustment_amount)} />
        <SummaryCard label="TOTAL" value={formatCurrency(invoice.total_amount)} color="#1E3A8A" />
        <SummaryCard label="PAID" value={formatCurrency(invoice.amount_paid)} />
        <SummaryCard
          label="BALANCE DUE"
          value={formatCurrency(invoice.balance_due)}
          color={invoice.balance_due > 0 ? '#B45309' : '#15803D'}
        />
      </Stack>

      <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        <Box sx={{ p: 2, backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
          <Typography sx={{ fontWeight: 700 }}>Line Items</Typography>
        </Box>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>Garment</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Code</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Qty</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Unit Price</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Line Total</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {invoice.items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                    <Typography sx={{ color: '#64748B' }}>No line items on this invoice.</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                invoice.items.map((item) => (
                  <TableRow key={item.id} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                    <TableCell>
                      <Typography variant="body2">{item.garment_type}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{item.garment_code}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{item.quantity}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{formatCurrency(item.unit_price)}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {formatCurrency(item.line_total)}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        <Box sx={{ p: 2, backgroundColor: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
          <Typography sx={{ fontWeight: 700 }}>Payment History</Typography>
        </Box>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Amount</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Method</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Reference</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Notes</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Recorded By</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {payments.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    <Typography sx={{ color: '#64748B' }}>No payments recorded yet.</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                payments.map((payment) => (
                  <TableRow key={payment.id} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                    <TableCell>
                      <Typography variant="body2">{formatDate(payment.payment_date)}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {formatCurrency(payment.amount)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{payment.payment_method_display}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{payment.reference || '-'}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ maxWidth: 220 }}>
                        {payment.notes || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{payment.recorded_by_name || '-'}</Typography>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {canRecord && (
        <>
          <RecordCustomerPaymentDialog
            open={paymentDialogOpen}
            onClose={() => setPaymentDialogOpen(false)}
            submit={handleRecordPayment}
            invoice={invoice}
          />
          <RecordCustomerPaymentDialog
            open={settleDialogOpen}
            onClose={() => setSettleDialogOpen(false)}
            submit={handleRecordPayment}
            invoice={invoice}
            settleInFull
          />
        </>
      )}
    </Box>
  );
};
