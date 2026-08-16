import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
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
import { useOrder } from '../hooks/useOrders';
import { useInvoiceEligibleOrders } from '../hooks/useInvoices';
import { formatCurrency } from '../utils/formatters';
import type { InvoiceCreatePayload } from '../types/billing';

const createInvoiceSchema = z.object({
  order: z.coerce.number({ required_error: 'Select an order' }).positive('Select an order'),
  invoice_date: z.string().min(1, 'Invoice date is required'),
  notes: z.string().max(4000, 'Notes must be 4000 characters or fewer'),
});

type CreateInvoiceFormData = z.infer<typeof createInvoiceSchema>;

interface CreateInvoiceDialogProps {
  open: boolean;
  onClose: () => void;
  submit: (payload: InvoiceCreatePayload) => Promise<unknown>;
}

export const CreateInvoiceDialog: React.FC<CreateInvoiceDialogProps> = ({
  open,
  onClose,
  submit,
}) => {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [orderSearch, setOrderSearch] = useState('');
  const [selectedOrderId, setSelectedOrderId] = useState<number | ''>('');

  const { data: eligibleOrdersData, isLoading: ordersLoading } = useInvoiceEligibleOrders({
    search: orderSearch,
  });
  const { data: order } = useOrder(selectedOrderId === '' ? 0 : Number(selectedOrderId));

  const {
    control,
    handleSubmit,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<CreateInvoiceFormData>({
    resolver: zodResolver(createInvoiceSchema),
    defaultValues: {
      order: 0,
      invoice_date: dayjs().format('YYYY-MM-DD'),
      notes: '',
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        order: 0,
        invoice_date: dayjs().format('YYYY-MM-DD'),
        notes: '',
      });
      setOrderSearch('');
      setSelectedOrderId('');
      setSubmitError(null);
    }
  }, [open, reset]);

  const orders = useMemo(() => eligibleOrdersData?.results ?? [], [eligibleOrdersData]);

  const handleOrderChange = (value: number | '') => {
    setSelectedOrderId(value);
    setValue('order', value === '' ? 0 : value, { shouldValidate: true });
  };

  const onSubmit = async (data: CreateInvoiceFormData) => {
    setSubmitError(null);
    try {
      await submit({
        order: data.order,
        invoice_date: data.invoice_date,
        notes: data.notes,
      });
      onClose();
    } catch (error) {
      setSubmitError(getApiErrorMessage(error));
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle sx={{ fontWeight: 700 }}>Create Invoice</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5} sx={{ mt: 0.5 }}>
          {submitError && <Alert severity="error">{submitError}</Alert>}

          <TextField
            label="Search order"
            placeholder="Order number or customer name"
            value={orderSearch}
            onChange={(event) => {
              setOrderSearch(event.target.value);
              handleOrderChange('');
            }}
            size="small"
            fullWidth
          />

          <FormControl fullWidth size="small" error={!!errors.order}>
            <InputLabel>Order *</InputLabel>
            <Select
              value={selectedOrderId}
              label="Order *"
              onChange={(event) => handleOrderChange(event.target.value as number | '')}
            >
              {ordersLoading ? (
                <MenuItem value="">Loading…</MenuItem>
              ) : (
                orders.map((entry) => (
                  <MenuItem key={entry.id} value={entry.id}>
                    {entry.order_number} · {entry.customer.full_name}
                  </MenuItem>
                ))
              )}
            </Select>
            {errors.order && <FormHelperText>{errors.order.message}</FormHelperText>}
          </FormControl>

          {order && (
            <Paper
              variant="outlined"
              sx={{ p: 2, borderRadius: '10px', backgroundColor: '#FBF6EA' }}
            >
              <Stack spacing={1}>
                <Typography variant="caption" sx={{ color: '#6B6B6B' }}>
                  Order {order.order_number} · {order.items.length} garment line(s)
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 700 }}>
                  Total: {formatCurrency(Number(order.total_amount))}
                </Typography>
              </Stack>
            </Paper>
          )}

          <Controller
            name="invoice_date"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Invoice Date *"
                type="date"
                fullWidth
                size="small"
                InputLabelProps={{ shrink: true }}
                error={!!errors.invoice_date}
                helperText={errors.invoice_date?.message}
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
      <DialogActions
        sx={{
          px: { xs: 2, sm: 3 },
          py: 2,
          flexDirection: { xs: 'column-reverse', sm: 'row' },
          gap: 1,
        }}
      >
        <Button onClick={onClose} color="inherit" fullWidth>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit(onSubmit)}
          variant="contained"
          disabled={isSubmitting}
          startIcon={isSubmitting ? <CircularProgress size={16} color="inherit" /> : undefined}
          fullWidth
        >
          Create Invoice
        </Button>
      </DialogActions>
    </Dialog>
  );
};
