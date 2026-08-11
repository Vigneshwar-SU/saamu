import React, { useState } from 'react';
import {
  Box,
  Button,
  Link,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import PaymentsIcon from '@mui/icons-material/Payments';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import LocalPrintshopIcon from '@mui/icons-material/LocalPrintshop';
import CurrencyExchangeIcon from '@mui/icons-material/CurrencyExchange';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatCurrency, formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { RecordCustomerPaymentDialog } from '../components/RecordCustomerPaymentDialog';
import { useCreatePayment, useInvoice, useInvoicePayments } from '../hooks/useInvoices';
import { INVOICE_STATUS_LABELS, PAYMENT_TYPE_LABELS } from '../types/billing';
import type { CustomerPaymentPayload } from '../types/billing';
import { PageHeader } from '../components/ui/PageHeader';
import { SectionCard } from '../components/ui/SectionCard';
import { TableCard } from '../components/ui/TableCard';
import { TableStateRow } from '../components/ui/TableStateRow';
import { StatCard } from '../components/ui/StatCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { ErrorState } from '../components/ui/ErrorState';
import type { StatusTone } from '../components/ui/StatusBadge';

const INVOICE_TONES: Record<string, StatusTone> = {
  UNPAID: 'error',
  PARTIALLY_PAID: 'warning',
  PAID: 'success',
};

const PAYMENT_TYPE_TONES: Record<string, StatusTone> = {
  ADVANCE: 'info',
  PARTIAL: 'gold',
  FINAL: 'success',
  REFUND: 'error',
};

export const InvoiceDetail: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const invoiceId = Number(id ?? 0);
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [settleDialogOpen, setSettleDialogOpen] = useState(false);
  const [refundDialogOpen, setRefundDialogOpen] = useState(false);

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
        <Typography color="text.secondary">Loading invoice…</Typography>
      </Box>
    );
  }

  if (isError || !invoice) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, alignItems: 'flex-start' }}>
        <ErrorState message={getApiErrorMessage(error)} onRetry={() => refetch()} />
      </Box>
    );
  }

  const canRecord = isStaff && invoice.balance_due > 0;
  const canRefund = isStaff && invoice.amount_paid > 0;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <PageHeader
        title={invoice.invoice_number}
        subtitle={`${invoice.payment_count} payment${invoice.payment_count === 1 ? '' : 's'}`}
        icon={<ReceiptLongIcon />}
        backTo="/invoices"
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Invoices', to: '/invoices' }, { label: invoice.invoice_number }]}
        actions={
          <Stack direction="row" spacing={1} flexWrap="wrap">
            <Button
              variant="outlined"
              startIcon={<LocalPrintshopIcon />}
              onClick={() => navigate(`/invoices/${invoice.id}/bill`)}
            >
              View Bill
            </Button>
            {canRecord && (
              <>
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
                >
                  Settle in Full
                </Button>
              </>
            )}
            {canRefund && (
              <Button
                variant="outlined"
                color="error"
                startIcon={<CurrencyExchangeIcon />}
                onClick={() => setRefundDialogOpen(true)}
              >
                Record Refund
              </Button>
            )}
          </Stack>
        }
      />

      <SectionCard noPadding>
        <Box sx={{ px: 2.5, py: 2 }}>
          <Stack spacing={1}>
            <Stack direction="row" spacing={4} flexWrap="wrap">
              <Box>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
                  STATUS
                </Typography>
                <Box sx={{ mt: 0.5 }}>
                  <StatusBadge
                    label={INVOICE_STATUS_LABELS[invoice.status]}
                    tone={INVOICE_TONES[invoice.status] ?? 'neutral'}
                  />
                </Box>
              </Box>
              <Box>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
                  CUSTOMER
                </Typography>
                <Typography sx={{ fontWeight: 600 }}>{invoice.customer.full_name}</Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  {invoice.customer.mobile_number}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
                  ORDER
                </Typography>
                <Link
                  underline="hover"
                  color="inherit"
                  href={`/orders/${invoice.order.id}`}
                  onClick={(event) => {
                    event.preventDefault();
                    navigate(`/orders/${invoice.order.id}`);
                  }}
                  sx={{ fontWeight: 600, fontSize: '0.9rem' }}
                >
                  {invoice.order.order_number}
                </Link>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  {formatDate(invoice.order.order_date)}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
                  INVOICE DATE
                </Typography>
                <Typography sx={{ fontWeight: 600 }}>{formatDate(invoice.invoice_date)}</Typography>
              </Box>
              {invoice.created_by_name && (
                <Box>
                  <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
                    CREATED BY
                  </Typography>
                  <Typography sx={{ fontWeight: 600 }}>{invoice.created_by_name}</Typography>
                </Box>
              )}
            </Stack>
            {invoice.notes && (
              <Typography
                variant="body2"
                sx={{
                  color: 'text.secondary',
                  whiteSpace: 'pre-wrap',
                  mt: 1,
                  pt: 1,
                  borderTop: '1px solid #E7E0D0',
                }}
              >
                {invoice.notes}
              </Typography>
            )}
          </Stack>
        </Box>
      </SectionCard>

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' },
        }}
      >
        <StatCard label="Subtotal" value={formatCurrency(invoice.subtotal)} tone="default" />
        <StatCard label="Adjustment" value={formatCurrency(invoice.adjustment_amount)} tone="default" />
        <StatCard label="Total" value={formatCurrency(invoice.total_amount)} tone="gold" />
        <StatCard label="Gross Paid" value={formatCurrency(invoice.gross_paid)} tone="default" />
        <StatCard label="Refunded" value={formatCurrency(invoice.refunded_amount)} tone="error" />
        <StatCard label="Paid (Net)" value={formatCurrency(invoice.amount_paid)} tone="success" />
        <StatCard
          label="Balance Due"
          value={formatCurrency(invoice.balance_due)}
          tone={invoice.balance_due > 0 ? 'warning' : 'success'}
        />
      </Box>

      <SectionCard title="Line Items" icon={<ReceiptLongIcon />} noPadding>
        <TableCard sx={{ border: 'none', borderRadius: 0 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Garment</TableCell>
                <TableCell>Code</TableCell>
                <TableCell>Qty</TableCell>
                <TableCell>Unit Price</TableCell>
                <TableCell>Line Total</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {invoice.items.length === 0 ? (
                <TableStateRow
                  colSpan={5}
                  state="empty"
                  emptyTitle="No line items"
                  emptyMessage="No line items on this invoice."
                />
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
        </TableCard>
      </SectionCard>

      <SectionCard title="Payment History" icon={<PaymentsIcon />} noPadding>
        <TableCard sx={{ border: 'none', borderRadius: 0 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Amount</TableCell>
                <TableCell>Method</TableCell>
                <TableCell>Reference</TableCell>
                <TableCell>Notes</TableCell>
                <TableCell>Recorded By</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {payments.length === 0 ? (
                <TableStateRow
                  colSpan={7}
                  state="empty"
                  emptyTitle="No payments recorded yet"
                  emptyMessage="Payments for this invoice will appear here."
                />
              ) : (
                payments.map((payment) => (
                  <TableRow key={payment.id} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                    <TableCell>
                      <Typography variant="body2">{formatDate(payment.payment_date)}</Typography>
                    </TableCell>
                    <TableCell>
                      <StatusBadge
                        label={PAYMENT_TYPE_LABELS[payment.payment_type]}
                        tone={PAYMENT_TYPE_TONES[payment.payment_type] ?? 'neutral'}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight: 600,
                          color: payment.payment_type === 'REFUND' ? '#8F2F22' : 'inherit',
                        }}
                      >
                        {payment.payment_type === 'REFUND' ? '− ' : ''}
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
        </TableCard>
      </SectionCard>

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
      {canRefund && (
        <RecordCustomerPaymentDialog
          open={refundDialogOpen}
          onClose={() => setRefundDialogOpen(false)}
          submit={handleRecordPayment}
          invoice={invoice}
          refundMode
          payments={payments}
        />
      )}
    </Box>
  );
};

export default InvoiceDetail;
