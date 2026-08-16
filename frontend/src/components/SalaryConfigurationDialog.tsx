import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Checkbox,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  FormHelperText,
  InputLabel,
  MenuItem,
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
import { useTailorList } from '../hooks/useTailors';
import { SALARY_MODEL_LABELS, SALARY_MODELS } from '../types/payroll';
import type {
  SalaryConfigurationPayload,
  SalaryModel,
  TailorSalaryConfiguration,
} from '../types/payroll';

const salaryConfigSchema = z
  .object({
    tailor: z.number({ required_error: 'Select a tailor' }).positive('Select a tailor'),
    salary_model: z.enum(SALARY_MODELS, { required_error: 'Select a salary model' }),
    fixed_salary_amount: z.coerce
      .number({ required_error: 'Fixed salary is required' })
      .min(0, 'Fixed salary cannot be negative'),
    effective_from: z.string().min(1, 'Effective from date is required'),
    effective_to: z.string(),
    is_active: z.boolean(),
    notes: z.string().max(2000, 'Notes must be 2000 characters or fewer'),
  })
  .refine(
    (data) => {
      if (data.salary_model === 'FIXED_SALARY' || data.salary_model === 'MIXED') {
        return data.fixed_salary_amount > 0;
      }
      return true;
    },
    {
      path: ['fixed_salary_amount'],
      message: 'A positive fixed salary is required for this model',
    }
  );

type SalaryConfigFormData = z.infer<typeof salaryConfigSchema>;

interface SalaryConfigurationDialogProps {
  open: boolean;
  onClose: () => void;
  submit: (payload: SalaryConfigurationPayload) => Promise<unknown>;
  config?: TailorSalaryConfiguration | null;
}

export const SalaryConfigurationDialog: React.FC<SalaryConfigurationDialogProps> = ({
  open,
  onClose,
  submit,
  config,
}) => {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const { data: tailorsData } = useTailorList({ scope: 'all', page_size: 100 });

  const tailors = useMemo(() => tailorsData?.results ?? [], [tailorsData]);

  const {
    control,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<SalaryConfigFormData>({
    resolver: zodResolver(salaryConfigSchema),
    defaultValues: {
      tailor: 0,
      salary_model: 'PER_GARMENT',
      fixed_salary_amount: 0,
      effective_from: dayjs().format('YYYY-MM-DD'),
      effective_to: '',
      is_active: true,
      notes: '',
    },
  });

  const salaryModel = watch('salary_model');
  const requiresFixedSalary = salaryModel === 'FIXED_SALARY' || salaryModel === 'MIXED';

  useEffect(() => {
    if (open) {
      reset({
        tailor: config?.tailor.id ?? 0,
        salary_model: config?.salary_model ?? 'PER_GARMENT',
        fixed_salary_amount: config?.fixed_salary_amount ?? 0,
        effective_from: config?.effective_from ?? dayjs().format('YYYY-MM-DD'),
        effective_to: config?.effective_to ?? '',
        is_active: config?.is_active ?? true,
        notes: config?.notes ?? '',
      });
      setSubmitError(null);
    }
  }, [open, config, reset]);

  const onSubmit = async (data: SalaryConfigFormData) => {
    setSubmitError(null);
    try {
      await submit({
        tailor: data.tailor,
        salary_model: data.salary_model,
        fixed_salary_amount: data.fixed_salary_amount,
        effective_from: data.effective_from,
        effective_to: data.effective_to || null,
        is_active: data.is_active,
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
        {config ? 'Edit Salary Configuration' : 'Configure Tailor Salary'}
      </DialogTitle>
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
                  {tailors.map((tailor) => (
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
            name="salary_model"
            control={control}
            render={({ field }) => (
              <FormControl fullWidth size="small" error={!!errors.salary_model}>
                <InputLabel>Salary Model *</InputLabel>
                <Select
                  {...field}
                  label="Salary Model *"
                  value={field.value}
                  onChange={(event) => field.onChange(event.target.value as SalaryModel)}
                >
                  {SALARY_MODELS.map((model) => (
                    <MenuItem key={model} value={model}>
                      {SALARY_MODEL_LABELS[model]}
                    </MenuItem>
                  ))}
                </Select>
                {errors.salary_model && (
                  <FormHelperText>{errors.salary_model.message}</FormHelperText>
                )}
              </FormControl>
            )}
          />

          <Controller
            name="fixed_salary_amount"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label={requiresFixedSalary ? 'Fixed Salary (INR) *' : 'Fixed Salary (INR)'}
                type="number"
                inputProps={{ min: 0, step: '0.01' }}
                fullWidth
                size="small"
                error={!!errors.fixed_salary_amount}
                helperText={
                  errors.fixed_salary_amount?.message ??
                  (requiresFixedSalary
                    ? 'Used as the fixed component for this period.'
                    : 'Not used for the per-garment model.')
                }
                disabled={!requiresFixedSalary}
              />
            )}
          />

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <Controller
              name="effective_from"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Effective From *"
                  type="date"
                  fullWidth
                  size="small"
                  InputLabelProps={{ shrink: true }}
                  error={!!errors.effective_from}
                  helperText={errors.effective_from?.message}
                />
              )}
            />
            <Controller
              name="effective_to"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Effective To"
                  type="date"
                  fullWidth
                  size="small"
                  InputLabelProps={{ shrink: true }}
                  error={!!errors.effective_to}
                  helperText={
                    errors.effective_to?.message ?? 'Leave blank for an open-ended configuration.'
                  }
                />
              )}
            />
          </Stack>

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

          <Controller
            name="is_active"
            control={control}
            render={({ field }) => (
              <FormControlLabel
                control={
                  <Checkbox
                    checked={field.value}
                    onChange={(event) => field.onChange(event.target.checked)}
                    size="small"
                  />
                }
                label={
                  <Typography variant="body2" sx={{ color: '#334155' }}>
                    Active configuration
                  </Typography>
                }
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
          {config ? 'Save Changes' : 'Add Configuration'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SalaryConfigurationDialog;
