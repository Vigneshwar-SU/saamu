import React, { useEffect, useState } from 'react';
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
import { INCOME_CATEGORIES, INCOME_CATEGORY_LABELS } from '../types/finance';
import type { IncomeCategory, IncomePayload } from '../types/finance';

const incomeSchema = z.object({
  category: z.string().min(1, 'Select a category'),
  amount: z.coerce
    .number({ required_error: 'Amount is required' })
    .positive('Amount must be greater than zero'),
  income_date: z.string().min(1, 'Income date is required'),
  reference: z.string().max(100, 'Reference must be 100 characters or fewer'),
  description: z.string().max(2000, 'Description must be 2000 characters or fewer'),
});

type IncomeFormData = z.infer<typeof incomeSchema>;

interface IncomeFormDialogProps {
  open: boolean;
  onClose: () => void;
  submit: (payload: IncomePayload) => Promise<unknown>;
}

export const IncomeFormDialog: React.FC<IncomeFormDialogProps> = ({
  open,
  onClose,
  submit,
}) => {
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<IncomeFormData>({
    resolver: zodResolver(incomeSchema),
    defaultValues: {
      category: '',
      amount: 0,
      income_date: dayjs().format('YYYY-MM-DD'),
      reference: '',
      description: '',
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        category: '',
        amount: 0,
        income_date: dayjs().format('YYYY-MM-DD'),
        reference: '',
        description: '',
      });
      setSubmitError(null);
    }
  }, [open, reset]);

  const onSubmit = async (data: IncomeFormData) => {
    setSubmitError(null);
    try {
      await submit({
        category: data.category as IncomeCategory,
        amount: data.amount,
        income_date: data.income_date,
        reference: data.reference,
        description: data.description,
      });
      onClose();
    } catch (error) {
      setSubmitError(getApiErrorMessage(error));
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle sx={{ fontWeight: 700 }}>Add Income</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5} sx={{ mt: 0.5 }}>
          {submitError && <Alert severity="error">{submitError}</Alert>}

          <Controller
            name="category"
            control={control}
            render={({ field }) => (
              <FormControl fullWidth size="small" error={!!errors.category}>
                <InputLabel>Category *</InputLabel>
                <Select
                  {...field}
                  label="Category *"
                  value={field.value}
                  onChange={(event) => field.onChange(event.target.value as IncomeCategory)}
                >
                  {INCOME_CATEGORIES.map((category) => (
                    <MenuItem key={category} value={category}>
                      {INCOME_CATEGORY_LABELS[category]}
                    </MenuItem>
                  ))}
                </Select>
                {errors.category && <FormHelperText>{errors.category.message}</FormHelperText>}
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
            name="income_date"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Income Date *"
                type="date"
                fullWidth
                size="small"
                InputLabelProps={{ shrink: true }}
                error={!!errors.income_date}
                helperText={errors.income_date?.message}
              />
            )}
          />

          <Controller
            name="reference"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Reference"
                placeholder="e.g. ORD-2026-0001"
                fullWidth
                size="small"
                error={!!errors.reference}
                helperText={errors.reference?.message}
              />
            )}
          />

          <Controller
            name="description"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Description"
                fullWidth
                variant="outlined"
                size="small"
                multiline
                minRows={2}
                error={!!errors.description}
                helperText={errors.description?.message}
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
          Save Income
        </Button>
      </DialogActions>
    </Dialog>
  );
};
