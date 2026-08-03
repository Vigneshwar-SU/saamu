import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormHelperText,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import dayjs from 'dayjs';
import { getApiErrorMessage } from '../utils/apiErrors';
import { formatCurrency } from '../utils/formatters';
import { PAYMENT_METHODS, PAYMENT_METHOD_LABELS } from '../types/billing';
import type { CustomerPaymentPayload, Invoice, PaymentMethod } from '../types/billing';

interface RecordCustomerPaymentDialogProps {
  open: boolean;
  onClose: () => void;
  submit: (payload: CustomerPaymentPayload) => Promise<unknown>;
  invoice: Invoice;
  settleInFull?: boolean;
}

type PaymentFormData = {
  amount: number;
  payment_date: string;
  payment_method: PaymentMethod;
  reference: string;
  notes: string;
};

export const RecordCustomerPaymentDialog: React.FC<RecordCustomerPaymentDialogProps> = ({
  open,
  onClose,
  submit,
  invoice,
  settleInFull = false,
}) => {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const balanceDue = invoice.balance_due;

  const paymentSchema = useMemo(
    () =>
      z
        .object({
          amount: z.coerce
            .number({ required_error: 'Amount is required' })
            .positive('Amount must be greater than zero'),
          payment_date: z.string().min(1, 'Payment date is required'),
          payment_method: z.enum(PAYMENT_METHODS, { required_error: 'Select a method' }),
          reference: z.string().max(100, 'Reference must be 100 characters or fewer'),
          notes: z.string().max(2000, 'Notes must be 2000 characters or fewer'),
        })
        .superRefine((data, ctx) => {
          if (data.amount > balanceDue) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              path: ['amount'],
              message: `Amount cannot exceed the balance due of ${formatCurrency(balanceDue)}`,
            });
          }
        }),
    [balanceDue]
  );

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<PaymentFormData>({
    resolver: zodResolver(paymentSchema),
    defaultValues: {
      amount: 0,
      payment_date: dayjs().format('YYYY-MM-DD'),
      payment_method: 'CASH',
      reference: '',
      notes: '',
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        amount: settleInFull ? balanceDue : 0,
        payment_date: dayjs().format('YYYY-MM-DD'),
        payment_method: 'CASH',
        reference: '',
        notes: '',
      });
      setSubmitError(null);
    }
  }, [open, settleInFull, balanceDue, reset]);

  const onSubmit = async (data: PaymentFormData) => {
    setSubmitError(null);
    try {
      await submit({
        amount: data.amount,
        payment_date: data.payment_date,
        payment_method: data.payment_method,
        reference: data.reference,
        notes: data.notes,
      });
      onClose();
    } catch (error) {
      setSubmitError(getApiErrorMessage(error));
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle sx={{ fontWeight: 700 }}>
        {settleInFull ? 'Settle in Full' : 'Record Payment'}
      </DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5} sx={{ mt: 0.5 }}>
          {submitError && <Alert severity="error">{submitError}</Alert>}

          <Paper sx={{ p: 2, borderRadius: '12px', border: '1px solid #E2E8F0', backgroundColor: '#F8FAFC' }}>
            <Stack spacing={1}>
              <InvoiceRow label="Invoice Number" value={invoice.invoice_number} />
              <InvoiceRow label="Invoice Total" value={formatCurrency(invoice.total_amount)} />
              <InvoiceRow label="Amount Paid" value={formatCurrency(invoice.amount_paid)} />
              <InvoiceRow
                label="Balance Due"
                value={formatCurrency(balanceDue)}
                emphasis
              />
            </Stack>
          </Paper>

          <Controller
            name="amount"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Amount (INR) *"
                type="number"
                inputProps={{ min: 0, step: '0.01' }}
                fullWidth
                size="small"
                disabled={settleInFull}
                error={!!errors.amount}
                helperText={
                  errors.amount?.message ??
                  (settleInFull ? 'Pays the full balance due.' : undefined)
                }
              />
            )}
          />

          <Controller
            name="payment_date"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Payment Date *"
                type="date"
                fullWidth
                size="small"
                InputLabelProps={{ shrink: true }}
                error={!!errors.payment_date}
                helperText={errors.payment_date?.message}
              />
            )}
          />

          <Controller
            name="payment_method"
            control={control}
            render={({ field }) => (
              <FormControl fullWidth size="small" error={!!errors.payment_method}>
                <InputLabel>Payment Method *</InputLabel>
                <Select
                  {...field}
                  label="Payment Method *"
                  value={field.value}
                  onChange={(event) => field.onChange(event.target.value as PaymentMethod)}
                >
                  {PAYMENT_METHODS.map((method) => (
                    <MenuItem key={method} value={method}>
                      {PAYMENT_METHOD_LABELS[method]}
                    </MenuItem>
                  ))}
                </Select>
                {errors.payment_method && (
                  <FormHelperText>{errors.payment_method.message}</FormHelperText>
                )}
              </FormControl>
            )}
          />

          <Controller
            name="reference"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Reference"
                fullWidth
                size="small"
                placeholder="e.g. UPI transaction ID or bank reference"
                error={!!errors.reference}
                helperText={errors.reference?.message}
              />
            )}
          />

          <Controller
            name="notes"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Notes"
                fullWidth
                variant="outlined"
                size="small"
                multiline
                minRows={2}
                error={!!errors.notes}
                helperText={errors.notes?.message}
              />
            )}
          />
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} color="inherit">
          Cancel
        </Button>
        <Button
          onClick={handleSubmit(onSubmit)}
          variant="contained"
          disabled={isSubmitting}
          startIcon={isSubmitting ? <CircularProgress size={16} color="inherit" /> : undefined}
          sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
        >
          {settleInFull ? 'Settle in Full' : 'Record Payment'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const InvoiceRow: React.FC<{ label: string; value: string; emphasis?: boolean }> = ({
  label,
  value,
  emphasis,
}) => (
  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
    <Typography
      variant="body2"
      sx={{ color: emphasis ? '#0F172A' : '#64748B', fontWeight: emphasis ? 700 : 500 }}
    >
      {label}
    </Typography>
    <Typography
      variant="body2"
      sx={{ fontWeight: emphasis ? 800 : 600, color: emphasis ? '#1E3A8A' : '#0F172A' }}
    >
      {value}
    </Typography>
  </Box>
);
