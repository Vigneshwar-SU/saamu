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
  Select,
  Stack,
  TextField,
} from '@mui/material';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import dayjs from 'dayjs';
import { getApiErrorMessage } from '../utils/apiErrors';
import { useTailorList } from '../hooks/useTailors';
import type { AdvancePayload } from '../types/advances';

const advanceSchema = z.object({
  tailor: z.number({ required_error: 'Select a tailor' }).positive('Select a tailor'),
  amount: z.coerce
    .number({ required_error: 'Amount is required' })
    .positive('Amount must be greater than zero'),
  advance_date: z.string().min(1, 'Advance date is required'),
  notes: z.string().max(2000, 'Notes must be 2000 characters or fewer'),
});

type AdvanceFormData = z.infer<typeof advanceSchema>;

interface AddAdvanceDialogProps {
  open: boolean;
  onClose: () => void;
  submit: (payload: AdvancePayload) => Promise<unknown>;
  defaultTailorId?: number;
}

export const AddAdvanceDialog: React.FC<AddAdvanceDialogProps> = ({
  open,
  onClose,
  submit,
  defaultTailorId,
}) => {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const { data: tailorsData } = useTailorList({ scope: 'all', page_size: 100 });

  const activeTailors = useMemo(() => tailorsData?.results ?? [], [tailorsData]);

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<AdvanceFormData>({
    resolver: zodResolver(advanceSchema),
    defaultValues: {
      tailor: 0,
      amount: 0,
      advance_date: dayjs().format('YYYY-MM-DD'),
      notes: '',
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        tailor: defaultTailorId ?? 0,
        amount: 0,
        advance_date: dayjs().format('YYYY-MM-DD'),
        notes: '',
      });
      setSubmitError(null);
    }
  }, [open, defaultTailorId, reset]);

  const onSubmit = async (data: AdvanceFormData) => {
    setSubmitError(null);
    try {
      await submit({
        tailor: data.tailor,
        amount: data.amount,
        advance_date: data.advance_date,
        notes: data.notes,
      });
      onClose();
    } catch (error) {
      setSubmitError(getApiErrorMessage(error));
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle sx={{ fontWeight: 700 }}>Add Salary Advance</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5} sx={{ mt: 0.5 }}>
          {submitError && <Alert severity="error">{submitError}</Alert>}

          <Controller
            name="tailor"
            control={control}
            render={({ field }) => (
              <FormControl fullWidth size="small" error={!!errors.tailor}>
                <InputLabel>Tailor *</InputLabel>
                <Select
                  {...field}
                  label="Tailor *"
                  value={field.value}
                  onChange={(event) => field.onChange(event.target.value as number)}
                >
                  {activeTailors.map((tailor) => (
                    <MenuItem key={tailor.id} value={tailor.id}>
                      {tailor.name}
                      {tailor.is_active ? '' : ' (Archived)'}
                    </MenuItem>
                  ))}
                </Select>
                {errors.tailor && <FormHelperText>{errors.tailor.message}</FormHelperText>}
              </FormControl>
            )}
          />

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
                error={!!errors.amount}
                helperText={errors.amount?.message}
              />
            )}
          />

          <Controller
            name="advance_date"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Advance Date *"
                type="date"
                fullWidth
                size="small"
                InputLabelProps={{ shrink: true }}
                error={!!errors.advance_date}
                helperText={errors.advance_date?.message}
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
          Save Advance
        </Button>
      </DialogActions>
    </Dialog>
  );
};
