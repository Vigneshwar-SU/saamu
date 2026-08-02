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
import { getApiErrorMessage } from '../utils/apiErrors';
import { useCreateWorkAssignment, usePieceRates, useTailorList } from '../hooks/useTailors';
import { useOrder, useOrderList } from '../hooks/useOrders';
import { formatCurrency } from '../utils/formatters';
import type { OrderItem } from '../types/orders';

interface AssignWorkDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
  defaultTailorId?: number;
}

const AssignWorkDialog: React.FC<AssignWorkDialogProps> = ({ open, onClose, onCreated, defaultTailorId }) => {
  const { data: tailorsData } = useTailorList({ scope: 'active' });
  const { data: pieceRatesData } = usePieceRates();
  const createMutation = useCreateWorkAssignment();

  const [tailorId, setTailorId] = useState<number | ''>('');
  const [orderSearch, setOrderSearch] = useState('');
  const [orderId, setOrderId] = useState<number | ''>('');
  const [orderItemId, setOrderItemId] = useState<number | ''>('');
  const [quantity, setQuantity] = useState('');
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: ordersData } = useOrderList({ search: orderSearch });
  const { data: order } = useOrder(orderId === '' ? 0 : Number(orderId));

  useEffect(() => {
    if (open) {
      setTailorId(defaultTailorId ?? '');
      setOrderSearch('');
      setOrderId('');
      setOrderItemId('');
      setQuantity('');
      setSubmitError(null);
    }
  }, [open, defaultTailorId]);

  const activeTailors = useMemo(() => tailorsData?.results ?? [], [tailorsData]);
  const orders = useMemo(() => ordersData?.results ?? [], [ordersData]);

  const eligibleItems = useMemo(() => {
    if (!order) return [];
    return order.items.filter((item) => item.remaining_quantity > 0);
  }, [order]);

  const selectedItem = useMemo(() => {
    if (!order) return undefined;
    return order.items.find((item) => item.id === Number(orderItemId));
  }, [order, orderItemId]);

  const applicableRate = useMemo(() => {
    if (!selectedItem) return undefined;
    const rates = pieceRatesData?.results ?? [];
    return rates.find((rate) => rate.garment_type === selectedItem.garment_code && rate.is_active);
  }, [selectedItem, pieceRatesData]);

  const maxQuantity = selectedItem?.remaining_quantity ?? 0;

  const handleSubmit = async () => {
    setSubmitError(null);
    if (tailorId === '' || orderId === '' || orderItemId === '') {
      setSubmitError('Select a tailor, order, and garment.');
      return;
    }
    const quantityValue = Number(quantity);
    if (!Number.isInteger(quantityValue) || quantityValue < 1 || quantityValue > maxQuantity) {
      setSubmitError(`Assigned quantity must be between 1 and ${maxQuantity}.`);
      return;
    }
    if (!applicableRate) {
      setSubmitError('No active piece rate is configured for this garment. Configure it first.');
      return;
    }
    setIsSubmitting(true);
    try {
      await createMutation.mutateAsync({
        tailor: Number(tailorId),
        order: Number(orderId),
        order_item: Number(orderItemId),
        assigned_quantity: quantityValue,
      });
      onCreated();
      onClose();
    } catch (error) {
      setSubmitError(getApiErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle sx={{ fontWeight: 700 }}>Assign Work</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5} sx={{ mt: 0.5 }}>
          {submitError && <Alert severity="error">{submitError}</Alert>}

          <FormControl fullWidth size="small">
            <InputLabel>Tailor *</InputLabel>
            <Select
              value={tailorId}
              label="Tailor *"
              onChange={(event) => setTailorId(event.target.value as number | '')}
            >
              {activeTailors.map((tailor) => (
                <MenuItem key={tailor.id} value={tailor.id}>
                  {tailor.name}
                </MenuItem>
              ))}
            </Select>
            <FormHelperText>Only active tailors can receive work.</FormHelperText>
          </FormControl>

          <TextField
            label="Search order"
            placeholder="Order number or customer name"
            value={orderSearch}
            onChange={(event) => {
              setOrderSearch(event.target.value);
              setOrderId('');
              setOrderItemId('');
            }}
            size="small"
            fullWidth
          />

          <FormControl fullWidth size="small">
            <InputLabel>Order *</InputLabel>
            <Select
              value={orderId}
              label="Order *"
              onChange={(event) => {
                setOrderId(event.target.value as number | '');
                setOrderItemId('');
              }}
            >
              {orders.map((entry) => (
                <MenuItem key={entry.id} value={entry.id}>
                  {entry.order_number} · {entry.customer.full_name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {order && (
            <>
              <FormControl fullWidth size="small">
                <InputLabel>Garment to assign *</InputLabel>
                <Select
                  value={orderItemId}
                  label="Garment to assign *"
                  onChange={(event) => setOrderItemId(event.target.value as number | '')}
                >
                  {eligibleItems.map((item: OrderItem) => (
                    <MenuItem key={item.id} value={item.id}>
                      {item.garment_type} · remaining {item.remaining_quantity} of {item.quantity}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {selectedItem && (
                <Paper variant="outlined" sx={{ p: 2, borderRadius: '10px', backgroundColor: '#F8FAFC' }}>
                  <Typography variant="caption" sx={{ color: '#64748B', display: 'block', mb: 1 }}>
                    {selectedItem.garment_type} · {selectedItem.quantity} ordered ·{' '}
                    {selectedItem.remaining_quantity} remaining
                  </Typography>
                  <TextField
                    label="Assigned quantity *"
                    value={quantity}
                    onChange={(event) => setQuantity(event.target.value)}
                    size="small"
                    type="number"
                    fullWidth
                    inputProps={{ min: 1, max: maxQuantity }}
                    helperText={`Applicable piece rate: ${formatCurrency(applicableRate?.rate_per_piece ?? 0)}${
                      applicableRate ? '' : ' (not configured)'
                    }`}
                    error={applicableRate ? false : true}
                  />
                </Paper>
              )}
            </>
          )}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} color="inherit">
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={isSubmitting}
          startIcon={isSubmitting ? <CircularProgress size={16} color="inherit" /> : undefined}
          sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
        >
          Assign Work
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AssignWorkDialog;
