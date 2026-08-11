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
import { formatCurrency, formatDate } from '../utils/formatters';
import {
  PAYMENT_METHODS,
  PAYMENT_METHOD_LABELS,
  PAYMENT_TYPES,
  PAYMENT_TYPE_LABELS,
} from '../types/billing';
import type {
  CustomerPayment,
  CustomerPaymentPayload,
  Invoice,
  PaymentMethod,
  PaymentType,
} from '../types/billing';

interface RecordCustomerPaymentDialogProps {
  open: boolean;
  onClose: () => void;
  submit: (payload: CustomerPaymentPayload) => Promise<unknown>;
  invoice: Invoice;
  settleInFull?: boolean;
  refundMode?: boolean;
  payments?: CustomerPayment[];
}

type PaymentFormData = {
  amount: number;
  payment_date: string;
  payment_method: PaymentMethod;
  payment_type: PaymentType;
  refunded_payment: number | '';
  reference: string;
  notes: string;
};

export const RecordCustomerPaymentDialog: React.FC<RecordCustomerPaymentDialogProps> = ({
  open,
  onClose,
  submit,
  invoice,
  settleInFull = false,
  refundMode = false,
  payments = [],
}) => {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const balanceDue = invoice.balance_due;
  const amountPaid = invoice.amount_paid;

  const paymentSchema = useMemo(
    () =>
      z
        .object({
          amount: z.coerce
            .number({ required_error: 'Amount is required' })
            .positive('Amount must be greater than zero'),
          payment_date: z.string().min(1, 'Payment date is required'),
          payment_method: z.enum(PAYMENT_METHODS, { required_error: 'Select a method' }),
          payment_type: z.enum(PAYMENT_TYPES, { required_error: 'Select a type' }),
          refunded_payment: z.union([z.number(), z.literal('')]),
          reference: z.string().max(100, 'Reference must be 100 characters or fewer'),
          notes: z.string().max(2000, 'Notes must be 2000 characters or fewer'),
        })
        .superRefine((data, ctx) => {
          const amount = Math.round(data.amount * 100) / 100;
          const balance = Math.round(balanceDue * 100) / 100;
          const paid = Math.round(amountPaid * 100) / 100;

          if (refundMode) {
            if (amount > paid) {
              ctx.addIssue({
                code: z.ZodIssueCode.custom,
                path: ['amount'],
                message: `A refund cannot exceed the total paid of ${formatCurrency(amountPaid)}`,
              });
            }
            return;
          }

          if (data.payment_type === 'FINAL') {
            if (amount !== balance) {
              ctx.addIssue({
                code: z.ZodIssueCode.custom,
                path: ['amount'],
                message: `A FINAL payment must equal the balance due of ${formatCurrency(balanceDue)}`,
              });
            }
          } else if (data.payment_type === 'PARTIAL' && amount >= balance) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              path: ['amount'],
              message: `A PARTIAL payment must be less than the balance due of ${formatCurrency(balanceDue)}`,
            });
          } else if (amount > balance) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              path: ['amount'],
              message: `Amount cannot exceed the balance due of ${formatCurrency(balanceDue)}`,
            });
          }
        }),
    [balanceDue, amountPaid, refundMode]
  );

  const {
    control,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<PaymentFormData>({
    resolver: zodResolver(paymentSchema),
    defaultValues: {
      amount: 0,
      payment_date: dayjs().format('YYYY-MM-DD'),
      payment_method: 'CASH',
      payment_type: 'PARTIAL',
      refunded_payment: '',
      reference: '',
      notes: '',
    },
  });

  const selectedType = watch('payment_type');

  useEffect(() => {
    if (open) {
      reset({
        amount: settleInFull ? balanceDue : 0,
        payment_date: dayjs().format('YYYY-MM-DD'),
        payment_method: 'CASH',
        payment_type: refundMode ? 'REFUND' : settleInFull ? 'FINAL' : 'PARTIAL',
        refunded_payment: '',
        reference: '',
        notes: '',
      });
      setSubmitError(null);
    }
  }, [open, settleInFull, refundMode, balanceDue, reset]);

  const refundablePayments = payments.filter((payment) => payment.payment_type !== 'REFUND');

  const onSubmit = async (data: PaymentFormData) => {
    setSubmitError(null);
    try {
      await submit({
        amount: data.amount,
        payment_date: data.payment_date,
        payment_method: data.payment_method,
        payment_type: data.payment_type,
        refunded_payment: data.refunded_payment === '' ? null : data.refunded_payment,
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
        {refundMode ? 'Record Refund' : settleInFull ? 'Settle in Full' : 'Record Payment'}
      </DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5} sx={{ mt: 0.5 }}>
          {submitError && <Alert severity="error">{submitError}</Alert>}

          <Paper sx={{ p: 2, borderRadius: '12px', border: '1px solid #E7E0D0', backgroundColor: '#FBF6EA' }}>
            <Stack spacing={1}>
              <InvoiceRow label="Invoice Number" value={invoice.invoice_number} />
              <InvoiceRow label="Invoice Total" value={formatCurrency(invoice.total_amount)} />
              <InvoiceRow label="Amount Paid" value={formatCurrency(invoice.amount_paid)} />
              <InvoiceRow
                label={refundMode ? 'Total Paid (Refundable)' : 'Balance Due'}
                value={formatCurrency(refundMode ? amountPaid : balanceDue)}
                emphasis
              />
            </Stack>
          </Paper>

          <Controller
            name="payment_type"
            control={control}
            render={({ field }) => (
              <FormControl fullWidth size="small" error={!!errors.payment_type} disabled={refundMode}>
                <InputLabel>Payment Type *</InputLabel>
                <Select
                  {...field}
                  label="Payment Type *"
                  value={refundMode ? 'REFUND' : field.value}
                  onChange={(event) => field.onChange(event.target.value as PaymentType)}
                >
                  {PAYMENT_TYPES.map((type) => (
                    <MenuItem key={type} value={type}>
                      {PAYMENT_TYPE_LABELS[type]}
                    </MenuItem>
                  ))}
                </Select>
                {errors.payment_type && (
                  <FormHelperText>{errors.payment_type.message}</FormHelperText>
                )}
              </FormControl>
            )}
          />

          <Controller
            name="amount"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label={refundMode ? 'Refund Amount (INR) *' : 'Amount (INR) *'}
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

          {refundMode && (
            <Controller
              name="refunded_payment"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth size="small" error={!!errors.refunded_payment}>
                  <InputLabel>Original Payment (optional)</InputLabel>
                  <Select
                    {...field}
                    label="Original Payment (optional)"
                    value={field.value}
                    onChange={(event) =>
                      field.onChange(
                        event.target.value === ''
                          ? ''
                          : Number(event.target.value)
                      )
                    }
                  >
                    <MenuItem value="">— None —</MenuItem>
                    {refundablePayments.map((payment) => (
                      <MenuItem key={payment.id} value={payment.id}>
                        {formatDate(payment.payment_date)} •{' '}
                        {PAYMENT_TYPE_LABELS[payment.payment_type]} •{' '}
                        {formatCurrency(payment.amount)}
                      </MenuItem>
                    ))}
                  </Select>
                  <FormHelperText>
                    {errors.refunded_payment?.message ?? 'Link the refund to the original payment.'}
                  </FormHelperText>
                </FormControl>
              )}
            />
          )}

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

          {selectedType === 'REFUND' && !refundMode && (
            <Alert severity="info">
              Refunds reduce the total paid on this invoice. Use the Record Refund button on the
              invoice page.
            </Alert>
          )}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} color="inherit">
          Cancel
        </Button>
        <Button
          onClick={handleSubmit(onSubmit)}
          variant="contained"
          color={refundMode ? 'error' : 'primary'}
          disabled={isSubmitting}
          startIcon={isSubmitting ? <CircularProgress size={16} color="inherit" /> : undefined}
        >
          {refundMode ? 'Record Refund' : settleInFull ? 'Settle in Full' : 'Record Payment'}
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
      sx={{ color: emphasis ? '#242424' : '#6B6B6B', fontWeight: emphasis ? 700 : 500 }}
    >
      {label}
    </Typography>
    <Typography
      variant="body2"
      sx={{ fontWeight: emphasis ? 800 : 600, color: emphasis ? '#7A5E0C' : '#242424' }}
    >
      {value}
    </Typography>
  </Box>
);
