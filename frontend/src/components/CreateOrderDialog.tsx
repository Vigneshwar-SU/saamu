import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import dayjs from 'dayjs';
import { useCustomerList } from '../hooks/useCustomers';
import { useMeasurements } from '../hooks/useMeasurements';
import { useCreateOrder } from '../hooks/useOrders';
import { getApiErrorMessage } from '../utils/apiErrors';
import { MEASUREMENT_REQUIRED_FIELDS } from '../types/customers';
import type { Customer, GarmentType, Measurement } from '../types/customers';
import type { Order, OrderCreatePayload, OrderItemPayload } from '../types/orders';

const GARMENT_OPTIONS: Array<{ code: GarmentType; label: string }> = [
  { code: 'SHIRT', label: 'Shirt' },
  { code: 'PANT', label: 'Pant' },
];

const GARMENT_LABELS: Record<GarmentType, string> = {
  SHIRT: 'Shirt',
  PANT: 'Pant',
};

interface ItemDraft {
  key: number;
  garment_type: GarmentType;
  quantity: number;
  unit_price: string;
  measurement_id: number | null;
  notes: string;
}

interface CreateOrderDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated: (order: Order) => void;
}

let nextItemKey = 1;

const emptyItem = (): ItemDraft => ({
  key: nextItemKey++,
  garment_type: 'SHIRT',
  quantity: 1,
  unit_price: '',
  measurement_id: null,
  notes: '',
});

export const CreateOrderDialog: React.FC<CreateOrderDialogProps> = ({ open, onClose, onCreated }) => {
  const createMutation = useCreateOrder();

  const [customerId, setCustomerId] = useState<number | null>(null);
  const [customerInput, setCustomerInput] = useState('');
  const [customerDebounced, setCustomerDebounced] = useState('');
  const [items, setItems] = useState<ItemDraft[]>([emptyItem()]);
  const [notes, setNotes] = useState('');
  const [expectedDelivery, setExpectedDelivery] = useState('');
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [clientErrors, setClientErrors] = useState<string | null>(null);

  const { data: customerData, isFetching: customersFetching } = useCustomerList({
    search: customerDebounced,
    status: 'all',
  });
  const { data: measurements, isLoading: measurementsLoading } = useMeasurements(customerId ?? 0);

  useEffect(() => {
    const timer = setTimeout(() => setCustomerDebounced(customerInput.trim()), 300);
    return () => clearTimeout(timer);
  }, [customerInput]);

  useEffect(() => {
    if (open) {
      setCustomerId(null);
      setCustomerInput('');
      setCustomerDebounced('');
      setItems([emptyItem()]);
      setNotes('');
      setExpectedDelivery('');
      setSubmitError(null);
      setClientErrors(null);
    }
  }, [open]);

  const measurementOptionsByGarment = useMemo(() => {
    const byGarment: Record<GarmentType, Measurement[]> = { SHIRT: [], PANT: [] };
    for (const m of measurements ?? []) {
      if (m.garment_type in byGarment) {
        byGarment[m.garment_type].push(m);
      }
    }
    for (const garment of GARMENT_OPTIONS) {
      byGarment[garment.code].sort((a, b) => b.version - a.version);
    }
    return byGarment;
  }, [measurements]);

  const isMeasurementComplete = (measurement: Measurement): boolean => {
    const required = MEASUREMENT_REQUIRED_FIELDS[measurement.garment_type];
    return required.every((field) => measurement[field] != null);
  };

  const handleCustomerChange = (customer: Customer | null) => {
    setCustomerId(customer ? customer.id : null);
    setItems((current) =>
      current.map((item) => ({ ...item, measurement_id: null }))
    );
  };

  const handleGarmentChange = (key: number, garment: GarmentType) => {
    setItems((current) =>
      current.map((item) =>
        item.key === key ? { ...item, garment_type: garment, measurement_id: null } : item
      )
    );
  };

  const updateItem = (key: number, patch: Partial<ItemDraft>) => {
    setItems((current) => current.map((item) => (item.key === key ? { ...item, ...patch } : item)));
  };

  const addItem = () => setItems((current) => [...current, emptyItem()]);

  const removeItem = (key: number) => {
    setItems((current) => (current.length > 1 ? current.filter((item) => item.key !== key) : current));
  };

  const validate = (): OrderItemPayload[] | null => {
    if (!customerId) {
      setClientErrors('Select a customer for this order.');
      return null;
    }
    if (items.length === 0) {
      setClientErrors('Add at least one garment item.');
      return null;
    }
    const payloadItems: OrderItemPayload[] = [];
    for (const item of items) {
      if (!Number.isInteger(item.quantity) || item.quantity < 1) {
        setClientErrors('Each item must have a quantity of at least 1.');
        return null;
      }
      const price = Number(item.unit_price);
      if (item.unit_price === '' || Number.isNaN(price) || price < 0) {
        setClientErrors('Each item must have a valid unit price.');
        return null;
      }
      if (item.measurement_id == null) {
        setClientErrors(
          `Select a ${GARMENT_LABELS[item.garment_type]} measurement for every item.`
        );
        return null;
      }
      payloadItems.push({
        garment_type: item.garment_type,
        quantity: item.quantity,
        unit_price: price.toFixed(2),
        measurement_id: item.measurement_id,
        notes: item.notes.trim() || undefined,
      });
    }
    if (expectedDelivery && dayjs(expectedDelivery).isBefore(dayjs().format('YYYY-MM-DD'))) {
      setClientErrors('Expected delivery date cannot be earlier than today.');
      return null;
    }
    setClientErrors(null);
    return payloadItems;
  };

  const handleSubmit = async () => {
    setSubmitError(null);
    const payloadItems = validate();
    if (!payloadItems) return;
    const payload: OrderCreatePayload = {
      customer: customerId as number,
      notes: notes.trim() || undefined,
      expected_delivery_date: expectedDelivery || null,
      items: payloadItems,
    };
    try {
      const order = await createMutation.mutateAsync(payload);
      onCreated(order);
    } catch (error) {
      setSubmitError(getApiErrorMessage(error));
    }
  };

  const options = customerData?.results ?? [];

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle sx={{ fontWeight: 700 }}>Create New Order</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={3} sx={{ mt: 0.5 }}>
          {(submitError || clientErrors) && (
            <Alert severity="error">{submitError ?? clientErrors}</Alert>
          )}

          <Stack spacing={2.5}>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#1E3A8A' }}>
              Order Details
            </Typography>
            <Autocomplete
              value={options.find((customer) => customer.id === customerId) ?? null}
              onChange={(_event, value) => handleCustomerChange(value)}
              inputValue={customerInput}
              onInputChange={(_event, value) => setCustomerInput(value)}
              options={options}
              getOptionLabel={(customer) => `${customer.full_name} · ${customer.mobile_number}`}
              isOptionEqualToValue={(option, value) => option.id === value.id}
              loading={customersFetching}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Customer *"
                  placeholder="Search by name or mobile"
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <React.Fragment>
                        {customersFetching ? <CircularProgress size={18} /> : null}
                        {params.InputProps.endAdornment}
                      </React.Fragment>
                    ),
                  }}
                />
              )}
            />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Expected Delivery"
                type="date"
                value={expectedDelivery}
                onChange={(event) => setExpectedDelivery(event.target.value)}
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            </Stack>
            <TextField
              label="Order Notes"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              fullWidth
              multiline
              minRows={2}
            />
          </Stack>

          <Box>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#1E3A8A' }}>
                Garment Items
              </Typography>
              <Button size="small" startIcon={<AddIcon />} onClick={addItem} disabled={!customerId}>
                Add Item
              </Button>
            </Stack>

            {!customerId ? (
              <Alert severity="info" sx={{ mb: 1 }}>
                Select a customer to load their measurement chart.
              </Alert>
            ) : (
              <Stack spacing={2}>
                {items.map((item, index) => {
                  const measurementOptions = measurementOptionsByGarment[item.garment_type];
                  return (
                    <Box
                      key={item.key}
                      sx={{
                        p: 2,
                        border: '1px solid #E2E8F0',
                        borderRadius: '10px',
                        backgroundColor: '#F8FAFC',
                      }}
                    >
                      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5 }}>
                        <Typography variant="body2" sx={{ fontWeight: 700, color: '#475569' }}>
                          Item {index + 1}
                        </Typography>
                        <Button
                          size="small"
                          color="inherit"
                          startIcon={<DeleteOutlineIcon fontSize="small" />}
                          onClick={() => removeItem(item.key)}
                          disabled={items.length === 1}
                        >
                          Remove
                        </Button>
                      </Stack>
                      <Stack spacing={2}>
                        <FormControl size="small" fullWidth>
                          <InputLabel>Garment</InputLabel>
                          <Select
                            value={item.garment_type}
                            label="Garment"
                            onChange={(event) =>
                              handleGarmentChange(item.key, event.target.value as GarmentType)
                            }
                          >
                            {GARMENT_OPTIONS.map((garment) => (
                              <MenuItem key={garment.code} value={garment.code}>
                                {garment.label}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                        <FormControl size="small" fullWidth>
                          <InputLabel>Measurement Version</InputLabel>
                          <Select
                            value={item.measurement_id ?? ''}
                            label="Measurement Version"
                            onChange={(event) =>
                              updateItem(item.key, {
                                measurement_id: Number(event.target.value),
                              })
                            }
                            disabled={measurementsLoading}
                          >
                            {measurementOptions.length === 0 ? (
                              <MenuItem value="" disabled>
                                No {GARMENT_LABELS[item.garment_type]} measurements recorded
                              </MenuItem>
                            ) : (
                              measurementOptions.map((measurement) => {
                                const complete = isMeasurementComplete(measurement);
                                const label = `V${measurement.version}${measurement.is_current ? ' (Current)' : ''}${complete ? '' : ' · Incomplete'}`;
                                return (
                                  <MenuItem
                                    key={measurement.id}
                                    value={measurement.id}
                                    disabled={!complete}
                                  >
                                    {label}
                                  </MenuItem>
                                );
                              })
                            )}
                          </Select>
                        </FormControl>
                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                          <TextField
                            label="Quantity *"
                            type="number"
                            size="small"
                            inputProps={{ min: 1 }}
                            value={item.quantity}
                            onChange={(event) =>
                              updateItem(item.key, { quantity: Number(event.target.value) })
                            }
                            sx={{ width: { xs: '100%', sm: 140 } }}
                          />
                          <TextField
                            label="Unit Price (INR) *"
                            type="number"
                            size="small"
                            inputProps={{ min: 0, step: '0.01' }}
                            value={item.unit_price}
                            onChange={(event) =>
                              updateItem(item.key, { unit_price: event.target.value })
                            }
                            sx={{ width: { xs: '100%', sm: 180 } }}
                          />
                        </Stack>
                        <TextField
                          label="Item Notes"
                          size="small"
                          value={item.notes}
                          onChange={(event) => updateItem(item.key, { notes: event.target.value })}
                          fullWidth
                        />
                      </Stack>
                    </Box>
                  );
                })}
              </Stack>
            )}
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} color="inherit">
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={createMutation.isPending || !customerId}
          startIcon={createMutation.isPending ? <CircularProgress size={16} color="inherit" /> : undefined}
          sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
        >
          Create Order
        </Button>
      </DialogActions>
    </Dialog>
  );
};
