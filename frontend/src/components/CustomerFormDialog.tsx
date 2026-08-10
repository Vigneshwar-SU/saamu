import React, { useEffect, useState } from 'react';
import {
  Alert,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
} from '@mui/material';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { normalizeApiError } from '../utils/apiErrors';
import { normalizeFullName, normalizeMobileNumber } from '../utils/normalization';
import type { Customer, CustomerPayload } from '../types/customers';

const MOBILE_REGEX = /^\+?[0-9]{10,15}$/;

const mobileField = z
  .string()
  .trim()
  .min(1, 'Mobile number is required')
  .transform((value) => normalizeMobileNumber(value))
  .refine((value) => MOBILE_REGEX.test(value), {
    message: 'Enter a valid mobile number (10-15 digits, optional leading +).',
  });

const customerSchema = z
  .object({
    full_name: z
      .string()
      .trim()
      .min(1, 'Full name is required')
      .max(200, 'Full name must be 200 characters or fewer')
      .transform((value) => normalizeFullName(value))
      .refine((value) => /[a-zA-Z]/.test(value), {
        message: 'Full name must contain at least one letter.',
      }),
    mobile_number: mobileField,
    alternate_mobile_number: z
      .string()
      .trim()
      .transform((value) => (value ? normalizeMobileNumber(value) : ''))
      .refine((value) => !value || MOBILE_REGEX.test(value), {
        message: 'Enter a valid mobile number (10-15 digits, optional leading +).',
      }),
    address: z.string().max(1000, 'Address must be 1000 characters or fewer'),
    notes: z.string().max(2000, 'Notes must be 2000 characters or fewer'),
  })
  .refine(
    (data) => !data.alternate_mobile_number || data.alternate_mobile_number !== data.mobile_number,
    {
      message: 'Alternate mobile must differ from the primary mobile.',
      path: ['alternate_mobile_number'],
    }
  );

const FIELD_KEYS = ['full_name', 'mobile_number', 'alternate_mobile_number', 'address', 'notes'] as const;

type CustomerFormData = z.infer<typeof customerSchema>;

interface CustomerFormDialogProps {
  open: boolean;
  initial: Customer | null;
  onClose: () => void;
  submit: (payload: CustomerPayload) => Promise<unknown>;
}

export const CustomerFormDialog: React.FC<CustomerFormDialogProps> = ({
  open,
  initial,
  onClose,
  submit,
}) => {
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<CustomerFormData>({
    resolver: zodResolver(customerSchema),
    defaultValues: {
      full_name: '',
      mobile_number: '',
      alternate_mobile_number: '',
      address: '',
      notes: '',
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        full_name: initial ? normalizeFullName(initial.full_name) : '',
        mobile_number: initial ? normalizeMobileNumber(initial.mobile_number) : '',
        alternate_mobile_number: initial?.alternate_mobile_number
          ? normalizeMobileNumber(initial.alternate_mobile_number)
          : '',
        address: initial?.address ?? '',
        notes: initial?.notes ?? '',
      });
      setSubmitError(null);
    }
  }, [open, initial, reset]);

  const onSubmit = async (data: CustomerFormData) => {
    setSubmitError(null);
    try {
      await submit({
        full_name: data.full_name,
        mobile_number: data.mobile_number,
        alternate_mobile_number: data.alternate_mobile_number,
        address: data.address,
        notes: data.notes,
      });
      onClose();
    } catch (error) {
      const apiError = normalizeApiError(error);
      setSubmitError(apiError.message);
      const details = apiError.details as Partial<Record<(typeof FIELD_KEYS)[number], string[]>> | undefined;
      const fieldKey = details ? FIELD_KEYS.find((key) => details[key]?.[0]) : undefined;
      if (fieldKey && details) {
        setError(fieldKey, { message: details[fieldKey]![0] });
      }
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle sx={{ fontWeight: 700 }}>
        {initial ? 'Edit Customer' : 'Add New Customer'}
      </DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5} sx={{ mt: 0.5 }}>
          {submitError && <Alert severity="error">{submitError}</Alert>}

          <Controller
            name="full_name"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Full Name *"
                fullWidth
                variant="outlined"
                error={!!errors.full_name}
                helperText={errors.full_name?.message}
              />
            )}
          />

          <Controller
            name="mobile_number"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Primary Mobile *"
                fullWidth
                variant="outlined"
                error={!!errors.mobile_number}
                helperText={errors.mobile_number?.message}
              />
            )}
          />

          <Controller
            name="alternate_mobile_number"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Alternate Mobile"
                fullWidth
                variant="outlined"
                error={!!errors.alternate_mobile_number}
                helperText={errors.alternate_mobile_number?.message}
              />
            )}
          />

          <Controller
            name="address"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Address"
                fullWidth
                variant="outlined"
                multiline
                minRows={2}
                error={!!errors.address}
                helperText={errors.address?.message}
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
          {initial ? 'Save Changes' : 'Create Customer'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
