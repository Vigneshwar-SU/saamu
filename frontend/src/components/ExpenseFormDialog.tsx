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
import { EXPENSE_CATEGORIES, EXPENSE_CATEGORY_LABELS } from '../types/finance';
import type { ExpenseCategory, ExpensePayload } from '../types/finance';

const expenseSchema = z.object({
  category: z.string().min(1, 'Select a category'),
  amount: z.coerce
    .number({ required_error: 'Amount is required' })
    .positive('Amount must be greater than zero'),
  expense_date: z.string().min(1, 'Expense date is required'),
  reference: z.string().max(100, 'Reference must be 100 characters or fewer'),
  description: z.string().max(2000, 'Description must be 2000 characters or fewer'),
});

type ExpenseFormData = z.infer<typeof expenseSchema>;

interface ExpenseFormDialogProps {
  open: boolean;
  onClose: () => void;
  submit: (payload: ExpensePayload) => Promise<unknown>;
}

export const ExpenseFormDialog: React.FC<ExpenseFormDialogProps> = ({
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
  } = useForm<ExpenseFormData>({
    resolver: zodResolver(expenseSchema),
    defaultValues: {
      category: '',
      amount: 0,
      expense_date: dayjs().format('YYYY-MM-DD'),
      reference: '',
      description: '',
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        category: '',
        amount: 0,
        expense_date: dayjs().format('YYYY-MM-DD'),
        reference: '',
        description: '',
      });
      setSubmitError(null);
    }
  }, [open, reset]);

  const onSubmit = async (data: ExpenseFormData) => {
    setSubmitError(null);
    try {
      await submit({
        category: data.category as ExpenseCategory,
        amount: data.amount,
        expense_date: data.expense_date,
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
      <DialogTitle sx={{ fontWeight: 700 }}>Add Expense</DialogTitle>
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
                  onChange={(event) => field.onChange(event.target.value as ExpenseCategory)}
                >
                  {EXPENSE_CATEGORIES.map((category) => (
                    <MenuItem key={category} value={category}>
                      {EXPENSE_CATEGORY_LABELS[category]}
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
            name="expense_date"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Expense Date *"
                type="date"
                fullWidth
                size="small"
                InputLabelProps={{ shrink: true }}
                error={!!errors.expense_date}
                helperText={errors.expense_date?.message}
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
                placeholder="e.g. INV-001"
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
          Save Expense
        </Button>
      </DialogActions>
    </Dialog>
  );
};
