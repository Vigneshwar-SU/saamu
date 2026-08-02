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
import { getApiErrorMessage } from '../utils/apiErrors';
import type { Tailor, TailorPayload } from '../types/tailors';

const MOBILE_REGEX = /^\+?[0-9]{10,15}$/;

const tailorSchema = z.object({
  name: z.string().trim().min(1, 'Tailor name is required').max(200, 'Tailor name must be 200 characters or fewer'),
  mobile_number: z
    .string()
    .trim()
    .refine((value) => !value || MOBILE_REGEX.test(value), {
      message: 'Enter a valid mobile number (10-15 digits, optional leading +).',
    }),
  notes: z.string().max(2000, 'Notes must be 2000 characters or fewer'),
});

type TailorFormData = z.infer<typeof tailorSchema>;

interface TailorFormDialogProps {
  open: boolean;
  initial: Tailor | null;
  onClose: () => void;
  submit: (payload: TailorPayload) => Promise<unknown>;
}

export const TailorFormDialog: React.FC<TailorFormDialogProps> = ({
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
    formState: { errors, isSubmitting },
  } = useForm<TailorFormData>({
    resolver: zodResolver(tailorSchema),
    defaultValues: { name: '', mobile_number: '', notes: '' },
  });

  useEffect(() => {
    if (open) {
      reset({
        name: initial?.name ?? '',
        mobile_number: initial?.mobile_number ?? '',
        notes: initial?.notes ?? '',
      });
      setSubmitError(null);
    }
  }, [open, initial, reset]);

  const onSubmit = async (data: TailorFormData) => {
    setSubmitError(null);
    try {
      await submit({
        name: data.name,
        mobile_number: data.mobile_number,
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
        {initial ? 'Edit Tailor' : 'Add New Tailor'}
      </DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5} sx={{ mt: 0.5 }}>
          {submitError && <Alert severity="error">{submitError}</Alert>}

          <Controller
            name="name"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Tailor Name *"
                fullWidth
                variant="outlined"
                error={!!errors.name}
                helperText={errors.name?.message}
              />
            )}
          />

          <Controller
            name="mobile_number"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Mobile Number"
                fullWidth
                variant="outlined"
                error={!!errors.mobile_number}
                helperText={errors.mobile_number?.message}
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
          {initial ? 'Save Changes' : 'Create Tailor'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
