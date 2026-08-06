import React from 'react';
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  CircularProgress,
  Divider,
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
import LocalPrintshopIcon from '@mui/icons-material/LocalPrintshop';
import StorefrontIcon from '@mui/icons-material/Storefront';
import { useNavigate, useParams } from 'react-router-dom';
import { getApiErrorMessage } from '../utils/apiErrors';
import { formatCurrency, formatDate } from '../utils/formatters';
import { useInvoiceBill } from '../hooks/useInvoices';
import { INVOICE_STATUS_COLORS, INVOICE_STATUS_LABELS, PAYMENT_TYPE_LABELS } from '../types/billing';
import type { InvoiceStatus, PaymentType } from '../types/billing';

const PAYMENT_TYPE_COLORS: Record<PaymentType, { bg: string; text: string }> = {
  ADVANCE: { bg: '#E0E7FF', text: '#4338CA' },
  PARTIAL: { bg: '#DBEAFE', text: '#1D4ED8' },
  FINAL: { bg: '#DCFCE7', text: '#15803D' },
  REFUND: { bg: '#FEE2E2', text: '#B91C1C' },
};

export const InvoiceBill: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const invoiceId = Number(id ?? 0);

  const { data, isLoading, isError, error, refetch } = useInvoiceBill(invoiceId);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress size={32} />
      </Box>
    );
  }

  if (isError || !data) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, alignItems: 'flex-start' }}>
        <Alert severity="error">{getApiErrorMessage(error)}</Alert>
        <Button size="small" variant="outlined" onClick={() => refetch()}>
          Retry
        </Button>
      </Box>
    );
  }

  const { bill } = data;
  const totals = bill.totals;
  const colors = INVOICE_STATUS_COLORS[totals.status as InvoiceStatus];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Box className="no-print" sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
          <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
            Saamu Tailors ERP
          </Link>
          <Link underline="hover" color="inherit" href="/invoices" sx={{ fontSize: '0.85rem' }}>
            Invoices
          </Link>
          <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
            {bill.bill_metadata.invoice_number} • Bill
          </Typography>
        </Breadcrumbs>
        <Stack direction="row" spacing={1.5}>
          <Button
            size="small"
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate(`/invoices/${invoiceId}`)}
          >
            Back to Invoice
          </Button>
          <Button
            size="small"
            variant="contained"
            startIcon={<LocalPrintshopIcon />}
            onClick={() => window.print()}
            sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
          >
            Print
          </Button>
        </Stack>
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
          border: '1px solid #E2E8F0',
          boxShadow: '0 10px 30px rgba(15, 23, 42, 0.08)',
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
                backgroundColor: '#1E3A8A',
                color: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <StorefrontIcon />
            </Box>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 800, color: '#0F172A' }}>
                {bill.shop.name}
              </Typography>
              {bill.shop.tagline && (
                <Typography variant="body2" sx={{ color: '#475569', fontStyle: 'italic' }}>
                  {bill.shop.tagline}
                </Typography>
              )}
            </Box>
          </Box>
          <Box sx={{ textAlign: { xs: 'left', md: 'right' } }}>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#1E3A8A', letterSpacing: 1 }}>
              BILL
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {bill.bill_metadata.invoice_number}
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              {formatDate(bill.bill_metadata.invoice_date)}
            </Typography>
          </Box>
        </Box>

        {(bill.shop.address || bill.shop.phone) && (
          <Box sx={{ mt: 1.5 }}>
            {bill.shop.address && (
              <Typography variant="body2" sx={{ color: '#64748B', whiteSpace: 'pre-line' }}>
                {bill.shop.address}
              </Typography>
            )}
            {bill.shop.phone && (
              <Typography variant="body2" sx={{ color: '#64748B' }}>
                {bill.shop.phone}
              </Typography>
            )}
            {bill.shop.established_year && (
              <Typography variant="body2" sx={{ color: '#64748B' }}>
                Serving since {bill.shop.established_year}
              </Typography>
            )}
          </Box>
        )}

        <Divider sx={{ my: 3 }} />

        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={4} flexWrap="wrap">
          <Box>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
              BILLED TO
            </Typography>
            <Typography sx={{ fontWeight: 700 }}>{bill.customer.full_name}</Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              {bill.customer.mobile_number}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
              ORDER
            </Typography>
            <Typography sx={{ fontWeight: 600 }}>{bill.order.order_number}</Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              {formatDate(bill.order.order_date)}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
              ORDER STATUS
            </Typography>
            <Chip
              label={bill.order.status}
              size="small"
              sx={{ mt: 0.5, fontWeight: 600, backgroundColor: '#F1F5F9', color: '#334155' }}
            />
          </Box>
        </Stack>

        <TableContainer sx={{ mt: 3 }}>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ backgroundColor: '#F8FAFC' }}>
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
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
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
                  <TableRow sx={{ backgroundColor: '#F8FAFC' }}>
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
                  {bill.payment_history.map((payment) => {
                    const typeColors = PAYMENT_TYPE_COLORS[payment.payment_type];
                    return (
                      <TableRow key={payment.id}>
                        <TableCell>
                          <Typography variant="body2">{formatDate(payment.payment_date)}</Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={PAYMENT_TYPE_LABELS[payment.payment_type]}
                            size="small"
                            sx={{ fontWeight: 600, backgroundColor: typeColors.bg, color: typeColors.text }}
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
                              color: payment.payment_type === 'REFUND' ? '#B91C1C' : 'inherit',
                            }}
                          >
                            {payment.payment_type === 'REFUND' ? '− ' : ''}
                            {formatCurrency(payment.amount)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}

        <Box
          sx={{
            mt: 4,
            pt: 3,
            borderTop: '2px solid #1E3A8A',
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
          <Typography variant="caption" sx={{ color: '#94A3B8' }}>
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
    <Typography variant="body2" sx={{ fontWeight: strong ? 700 : 500, color: strong ? '#0F172A' : '#64748B' }}>
      {label}
    </Typography>
    <Typography variant="body2" sx={{ fontWeight: strong ? 800 : 600, color: strong ? '#1E3A8A' : '#0F172A' }}>
      {value}
    </Typography>
  </Box>
);
