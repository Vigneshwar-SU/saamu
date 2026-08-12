import React from 'react';
import {
  Box,
  Button,
  Chip,
  Divider,
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
import LocalPrintshopIcon from '@mui/icons-material/LocalPrintshop';
import StorefrontIcon from '@mui/icons-material/Storefront';
import { useParams } from 'react-router-dom';
import { getApiErrorMessage } from '../utils/apiErrors';
import { formatCurrency, formatDate } from '../utils/formatters';
import { useInvoiceBill } from '../hooks/useInvoices';
import { INVOICE_STATUS_COLORS, INVOICE_STATUS_LABELS, PAYMENT_TYPE_LABELS } from '../types/billing';
import type { InvoiceStatus } from '../types/billing';
import { PageHeader } from '../components/ui/PageHeader';
import { ErrorState } from '../components/ui/ErrorState';
import { StatusBadge } from '../components/ui/StatusBadge';
import type { StatusTone } from '../components/ui/StatusBadge';

const PAYMENT_TYPE_TONES: Record<string, StatusTone> = {
  ADVANCE: 'info',
  PARTIAL: 'gold',
  FINAL: 'success',
  REFUND: 'error',
};

export const InvoiceBill: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const invoiceId = Number(id ?? 0);

  const { data, isLoading, isError, error, refetch } = useInvoiceBill(invoiceId);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <Typography color="text.secondary">Loading bill…</Typography>
      </Box>
    );
  }

  if (isError || !data) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, alignItems: 'flex-start' }}>
        <ErrorState message={getApiErrorMessage(error)} onRetry={() => refetch()} />
      </Box>
    );
  }

  const { bill } = data;
  const totals = bill.totals;
  const colors = INVOICE_STATUS_COLORS[totals.status as InvoiceStatus];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Box className="no-print">
        <PageHeader
          title={`${bill.bill_metadata.invoice_number} · Bill`}
          icon={<LocalPrintshopIcon />}
          backTo={`/invoices/${invoiceId}`}
          crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Invoices', to: '/invoices' }, { label: `${bill.bill_metadata.invoice_number} · Bill` }]}
          actions={
            <Button variant="contained" startIcon={<LocalPrintshopIcon />} onClick={() => window.print()}>
              Print
            </Button>
          }
        />
      </Box>

      <Paper
        id="printable-bill"
        className="print-bill"
        sx={{
          maxWidth: 860,
          width: '100%',
          mx: 'auto',
          p: { xs: 3, md: 5 },
          borderRadius: '16px',
          border: '1px solid #E7E0D0',
          boxShadow: '0 10px 30px rgba(58, 48, 20, 0.10)',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            flexWrap: 'wrap',
            gap: 2,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                width: 52,
                height: 52,
                borderRadius: '14px',
                backgroundColor: '#8F6E10',
                color: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <StorefrontIcon />
            </Box>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 800, color: '#242424' }}>
                {bill.shop.name}
              </Typography>
              {bill.shop.tagline && (
                <Typography variant="body2" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
                  {bill.shop.tagline}
                </Typography>
              )}
            </Box>
          </Box>
          <Box sx={{ textAlign: { xs: 'left', md: 'right' } }}>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#8F6E10', letterSpacing: 1 }}>
              BILL
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {bill.bill_metadata.invoice_number}
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              {formatDate(bill.bill_metadata.invoice_date)}
            </Typography>
          </Box>
        </Box>

        {(bill.shop.address || bill.shop.phone) && (
          <Box sx={{ mt: 1.5 }}>
            {bill.shop.address && (
              <Typography variant="body2" sx={{ color: 'text.secondary', whiteSpace: 'pre-line' }}>
                {bill.shop.address}
              </Typography>
            )}
            {bill.shop.phone && (
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                {bill.shop.phone}
              </Typography>
            )}
            {bill.shop.established_year && (
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                Serving since {bill.shop.established_year}
              </Typography>
            )}
          </Box>
        )}

        <Divider sx={{ my: 3 }} />

        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={4} flexWrap="wrap">
          <Box>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
              BILLED TO
            </Typography>
            <Typography sx={{ fontWeight: 700 }}>{bill.customer.full_name}</Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              {bill.customer.mobile_number}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
              ORDER
            </Typography>
            <Typography sx={{ fontWeight: 600 }}>{bill.order.order_number}</Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              {formatDate(bill.order.order_date)}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
              ORDER STATUS
            </Typography>
            <Chip
              label={bill.order.status}
              size="small"
              sx={{ mt: 0.5, fontWeight: 600, backgroundColor: '#F1EDE2', color: '#544A35' }}
            />
          </Box>
        </Stack>

        <TableContainer sx={{ mt: 3 }}>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ backgroundColor: '#FBF6EA' }}>
                <TableCell sx={{ fontWeight: 700 }}>Garment</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Qty</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Unit Price</TableCell>
                <TableCell sx={{ fontWeight: 700 }} align="right">
                  Line Total
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {bill.garments.map((garment) => (
                <TableRow key={`${garment.garment_code}-${garment.line_total}`}>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {garment.garment_type}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                      {garment.garment_code}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{garment.quantity}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{formatCurrency(garment.unit_price)}</Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {formatCurrency(garment.line_total)}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Stack spacing={1} sx={{ mt: 2, alignItems: 'flex-end' }}>
          <BillTotalRow label="Subtotal" value={formatCurrency(totals.subtotal)} />
          <BillTotalRow label="Adjustment" value={formatCurrency(totals.adjustment_amount)} />
          <BillTotalRow label="Total" value={formatCurrency(totals.total_amount)} strong />
          <Divider sx={{ width: 240 }} />
          <BillTotalRow label="Gross Paid" value={formatCurrency(totals.gross_paid)} />
          <BillTotalRow label="Refunded" value={formatCurrency(totals.refunded_amount)} />
          <BillTotalRow label="Amount Paid" value={formatCurrency(totals.amount_paid)} />
          <BillTotalRow label="Balance Due" value={formatCurrency(totals.balance_due)} strong />
        </Stack>

        {bill.payment_history.length > 0 && (
          <>
            <Typography sx={{ fontWeight: 700, mt: 4, mb: 1 }}>Payment History</Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ backgroundColor: '#FBF6EA' }}>
                    <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Type</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Method</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Reference</TableCell>
                    <TableCell sx={{ fontWeight: 700 }} align="right">
                      Amount
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {bill.payment_history.map((payment) => (
                    <TableRow key={payment.id}>
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
                        <Typography variant="body2">{payment.payment_method_display}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{payment.reference || '-'}</Typography>
                      </TableCell>
                      <TableCell align="right">
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
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}

        <Box
          sx={{
            mt: 4,
            pt: 3,
            borderTop: '2px solid #8F6E10',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 2,
          }}
        >
          <Chip
            label={INVOICE_STATUS_LABELS[totals.status as InvoiceStatus]}
            size="small"
            sx={{ fontWeight: 700, backgroundColor: colors.bg, color: colors.text }}
          />
          <Typography variant="caption" sx={{ color: 'text.disabled' }}>
            Generated on {formatDate(bill.bill_metadata.generated_at, 'DD MMM YYYY, hh:mm A')}
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};

const BillTotalRow: React.FC<{ label: string; value: string; strong?: boolean }> = ({
  label,
  value,
  strong,
}) => (
  <Box sx={{ width: 240, display: 'flex', justifyContent: 'space-between' }}>
    <Typography
      variant="body2"
      sx={{ fontWeight: strong ? 700 : 500, color: strong ? '#242424' : 'text.secondary' }}
    >
      {label}
    </Typography>
    <Typography
      variant="body2"
      sx={{ fontWeight: strong ? 800 : 600, color: strong ? '#8F6E10' : '#242424' }}
    >
      {value}
    </Typography>
  </Box>
);

export default InvoiceBill;
