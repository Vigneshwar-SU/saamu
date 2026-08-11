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
import dayjs from 'dayjs';
import { getApiErrorMessage } from '../utils/apiErrors';
import type { PayrollPeriodPayload } from '../types/payroll';

const periodSchema = z
  .object({
    period_start: z.string().min(1, 'Period start is required'),
    period_end: z.string().min(1, 'Period end is required'),
    notes: z.string().max(2000, 'Notes must be 2000 characters or fewer'),
  })
  .refine((data) => data.period_start <= data.period_end, {
    message: 'Period end must be on or after period start.',
    path: ['period_end'],
  });

type PeriodFormData = z.infer<typeof periodSchema>;

interface PayrollPeriodDialogProps {
  open: boolean;
  onClose: () => void;
  submit: (payload: PayrollPeriodPayload) => Promise<unknown>;
}

export const PayrollPeriodDialog: React.FC<PayrollPeriodDialogProps> = ({ open, onClose, submit }) => {
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<PeriodFormData>({
    resolver: zodResolver(periodSchema),
    defaultValues: {
      period_start: dayjs().startOf('month').format('YYYY-MM-DD'),
      period_end: dayjs().format('YYYY-MM-DD'),
      notes: '',
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        period_start: dayjs().startOf('month').format('YYYY-MM-DD'),
        period_end: dayjs().format('YYYY-MM-DD'),
        notes: '',
      });
      setSubmitError(null);
    }
  }, [open, reset]);

  const onSubmit = async (data: PeriodFormData) => {
    setSubmitError(null);
    try {
      await submit({
        period_start: data.period_start,
        period_end: data.period_end,
        notes: data.notes,
      });
      onClose();
    } catch (error) {
      setSubmitError(getApiErrorMessage(error));
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle sx={{ fontWeight: 700 }}>Create Payroll Period</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5} sx={{ mt: 0.5 }}>
          {submitError && <Alert severity="error">{submitError}</Alert>}

          <Controller
            name="period_start"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Period Start *"
                type="date"
                fullWidth
                size="small"
                InputLabelProps={{ shrink: true }}
                error={!!errors.period_start}
                helperText={errors.period_start?.message}
              />
            )}
          />

          <Controller
            name="period_end"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Period End *"
                type="date"
                fullWidth
                size="small"
                InputLabelProps={{ shrink: true }}
                error={!!errors.period_end}
                helperText={errors.period_end?.message}
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
          
        >
          Create Period
        </Button>
      </DialogActions>
    </Dialog>
  );
};
