import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  InputAdornment,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { getApiErrorMessage } from '../utils/apiErrors';
import {
  MEASUREMENT_FIELD_LABELS,
  MEASUREMENT_FIELDS_BY_GARMENT,
  MEASUREMENT_REQUIRED_FIELDS,
} from '../types/customers';
import type {
  GarmentType,
  Measurement,
  MeasurementFieldName,
  MeasurementPayload,
} from '../types/customers';

const numericFieldSchema = z
  .number()
  .min(0.1, 'Value must be between 0.1 and 300 inches')
  .max(300, 'Value must be between 0.1 and 300 inches');

const measurementSchema = z
  .object({
    garment_type: z.enum(['SHIRT', 'PANT']),
    notes: z.string().max(2000, 'Notes must be 2000 characters or fewer'),
    neck_circumference: numericFieldSchema.nullish(),
    chest_circumference: numericFieldSchema.nullish(),
    waist_circumference: numericFieldSchema.nullish(),
    shoulder_width: numericFieldSchema.nullish(),
    sleeve_length: numericFieldSchema.nullish(),
    sleeve_circumference: numericFieldSchema.nullish(),
    cuff_circumference: numericFieldSchema.nullish(),
    shirt_length: numericFieldSchema.nullish(),
    hip_circumference: numericFieldSchema.nullish(),
    thigh_circumference: numericFieldSchema.nullish(),
    knee_circumference: numericFieldSchema.nullish(),
    bottom_circumference: numericFieldSchema.nullish(),
    length: numericFieldSchema.nullish(),
  })
  .superRefine((data, ctx) => {
    for (const field of MEASUREMENT_REQUIRED_FIELDS[data.garment_type]) {
      if (data[field] == null) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: [field],
          message: `This field is required for ${data.garment_type}.`,
        });
      }
    }
  });

type MeasurementFormData = z.infer<typeof measurementSchema>;

const buildDefaultValues = (
  garment: GarmentType,
  measurement: Measurement | null
): MeasurementFormData => ({
  garment_type: garment,
  notes: measurement?.notes ?? '',
  neck_circumference: measurement?.neck_circumference ?? null,
  chest_circumference: measurement?.chest_circumference ?? null,
  waist_circumference: measurement?.waist_circumference ?? null,
  shoulder_width: measurement?.shoulder_width ?? null,
  sleeve_length: measurement?.sleeve_length ?? null,
  sleeve_circumference: measurement?.sleeve_circumference ?? null,
  cuff_circumference: measurement?.cuff_circumference ?? null,
  shirt_length: measurement?.shirt_length ?? null,
  hip_circumference: measurement?.hip_circumference ?? null,
  thigh_circumference: measurement?.thigh_circumference ?? null,
  knee_circumference: measurement?.knee_circumference ?? null,
  bottom_circumference: measurement?.bottom_circumference ?? null,
  length: measurement?.length ?? null,
});

interface MeasurementFormDialogProps {
  open: boolean;
  garmentType: GarmentType;
  lockGarment: boolean;
  initial: Measurement | null;
  onClose: () => void;
  submit: (payload: MeasurementPayload) => Promise<unknown>;
}

export const MeasurementFormDialog: React.FC<MeasurementFormDialogProps> = ({
  open,
  garmentType,
  lockGarment,
  initial,
  onClose,
  submit,
}) => {
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<MeasurementFormData>({
    resolver: zodResolver(measurementSchema),
    defaultValues: buildDefaultValues(garmentType, initial),
  });

  useEffect(() => {
    if (open) {
      reset(buildDefaultValues(garmentType, initial));
      setSubmitError(null);
    }
  }, [open, reset, garmentType, initial]);

  const selectedGarment = watch('garment_type');
  const visibleFields = MEASUREMENT_FIELDS_BY_GARMENT[selectedGarment];

  const renderField = (name: MeasurementFieldName) => {
    const required = MEASUREMENT_REQUIRED_FIELDS[selectedGarment].includes(name);
    return (
      <Controller
        key={name}
        name={name}
        control={control}
        render={({ field }) => (
          <TextField
            {...field}
            label={`${MEASUREMENT_FIELD_LABELS[name]}${required ? ' *' : ''}`}
            type="number"
            fullWidth
            variant="outlined"
            inputProps={{ step: 0.1, min: 0.1, max: 300 }}
            InputProps={{
              endAdornment: <InputAdornment position="end">in</InputAdornment>,
            }}
            error={!!errors[name]}
            helperText={errors[name]?.message}
            onChange={(event) => {
              const raw = event.target.value;
              field.onChange(raw === '' ? null : Number(raw));
            }}
            value={field.value ?? ''}
          />
        )}
      />
    );
  };

  const onSubmit = async (data: MeasurementFormData) => {
    setSubmitError(null);
    try {
      const payload: MeasurementPayload = { garment_type: data.garment_type };
      for (const field of MEASUREMENT_FIELDS_BY_GARMENT[data.garment_type]) {
        const value = data[field];
        if (value != null) {
          payload[field] = value;
        }
      }
      if (data.notes) {
        payload.notes = data.notes;
      }
      await submit(payload);
      onClose();
    } catch (error) {
      setSubmitError(getApiErrorMessage(error));
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle sx={{ fontWeight: 700 }}>
        {initial ? `New ${initial.garment_type} Measurement Version` : `Record ${garmentType} Measurements`}
      </DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5} sx={{ mt: 0.5 }}>
          {submitError && <Alert severity="error">{submitError}</Alert>}

          <Controller
            name="garment_type"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                select
                label="Garment Type"
                fullWidth
                disabled={lockGarment}
                sx={{ maxWidth: 240 }}
              >
                <MenuItem value="SHIRT">Shirt</MenuItem>
                <MenuItem value="PANT">Pant</MenuItem>
              </TextField>
            )}
          />

          <Typography variant="caption" sx={{ color: '#6B6B6B' }}>
            All measurements are in inches. Fields marked with * are required for{' '}
            {selectedGarment}.
          </Typography>

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                sm: 'repeat(2, 1fr)',
                md: 'repeat(3, 1fr)',
              },
              gap: 2,
            }}
          >
            {visibleFields.map((field) => renderField(field))}
          </Box>

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
          
        >
          {initial ? 'Save New Version' : 'Save Measurements'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
