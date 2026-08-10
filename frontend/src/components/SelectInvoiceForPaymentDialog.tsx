import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useInvoiceList } from '../hooks/useInvoices';
import { formatCurrency } from '../utils/formatters';
import { INVOICE_STATUS_LABELS } from '../types/billing';
import type { Invoice, InvoiceStatus } from '../types/billing';

export type PaymentRecordMode = 'PAYMENT' | 'REFUND';

const MODE_STATUSES: Record<PaymentRecordMode, InvoiceStatus[]> = {
  PAYMENT: ['UNPAID', 'PARTIALLY_PAID'],
  REFUND: ['PARTIALLY_PAID', 'PAID'],
};

interface SelectInvoiceForPaymentDialogProps {
  open: boolean;
  mode: PaymentRecordMode;
  onClose: () => void;
  onSelect: (invoice: Invoice) => void;
}

export const SelectInvoiceForPaymentDialog: React.FC<SelectInvoiceForPaymentDialogProps> = ({
  open,
  mode,
  onClose,
  onSelect,
}) => {
  const [search, setSearch] = useState('');
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<number | ''>('');

  useEffect(() => {
    if (open) {
      setSearch('');
      setSelectedInvoiceId('');
    }
  }, [open, mode]);

  const { data: firstStatusData, isLoading: firstStatusLoading } = useInvoiceList(
    { search: search || undefined, status: MODE_STATUSES[mode][0], page: 1 },
    open
  );
  const { data: secondStatusData, isLoading: secondStatusLoading, isError } = useInvoiceList(
    { search: search || undefined, status: MODE_STATUSES[mode][1], page: 1 },
    open
  );

  const invoices = useMemo(() => {
    const byId = new Map<number, Invoice>();
    (firstStatusData?.results ?? []).forEach((invoice) => byId.set(invoice.id, invoice));
    (secondStatusData?.results ?? []).forEach((invoice) => byId.set(invoice.id, invoice));
    return Array.from(byId.values());
  }, [firstStatusData, secondStatusData]);

  const isLoading = firstStatusLoading || secondStatusLoading;

  const selectedInvoice = useMemo(
    () => invoices.find((invoice) => invoice.id === selectedInvoiceId) ?? null,
    [invoices, selectedInvoiceId]
  );

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle sx={{ fontWeight: 700 }}>
        {mode === 'REFUND' ? 'Select Invoice for Refund' : 'Select Invoice for Payment'}
      </DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5} sx={{ mt: 0.5 }}>
          {isError && <Alert severity="error">Unable to load invoices. Please try again.</Alert>}

          <TextField
            label="Search invoice"
            placeholder="Invoice no, order no, or customer"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setSelectedInvoiceId('');
            }}
            size="small"
            fullWidth
          />

          <FormControl fullWidth size="small">
            <InputLabel>Invoice *</InputLabel>
            <Select
              value={selectedInvoiceId}
              label="Invoice *"
              onChange={(event) => setSelectedInvoiceId(event.target.value as number | '')}
            >
              {isLoading ? (
                <MenuItem value="">Loading…</MenuItem>
              ) : invoices.length === 0 ? (
                <MenuItem value="" disabled>
                  No eligible invoices found
                </MenuItem>
              ) : (
                invoices.map((invoice) => (
                  <MenuItem key={invoice.id} value={invoice.id}>
                    {invoice.invoice_number} · {invoice.customer.full_name} ·{' '}
                    {INVOICE_STATUS_LABELS[invoice.status]}
                  </MenuItem>
                ))
              )}
            </Select>
          </FormControl>

          {selectedInvoice && (
            <Paper
              variant="outlined"
              sx={{ p: 2, borderRadius: '10px', backgroundColor: '#F8FAFC' }}
            >
              <Stack spacing={1}>
                <Typography variant="caption" sx={{ color: '#64748B' }}>
                  {selectedInvoice.invoice_number} ·{' '}
                  {INVOICE_STATUS_LABELS[selectedInvoice.status]}
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: '#64748B' }}>
                    Invoice Total
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {formatCurrency(selectedInvoice.total_amount)}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ color: '#64748B' }}>
                    Amount Paid
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {formatCurrency(selectedInvoice.amount_paid)}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography
                    variant="body2"
                    sx={{ color: '#64748B', fontWeight: mode === 'REFUND' ? 600 : 400 }}
                  >
                    {mode === 'REFUND' ? 'Total Paid (Refundable)' : 'Balance Due'}
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{
                      fontWeight: 700,
                      color: mode === 'REFUND' ? '#1E3A8A' : '#B45309',
                    }}
                  >
                    {formatCurrency(
                      mode === 'REFUND'
                        ? selectedInvoice.amount_paid
                        : selectedInvoice.balance_due
                    )}
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          )}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} color="inherit">
          Cancel
        </Button>
        <Button
          variant="contained"
          disabled={!selectedInvoice}
          onClick={() => selectedInvoice && onSelect(selectedInvoice)}
          sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
        >
          Continue
        </Button>
      </DialogActions>
    </Dialog>
  );
};
