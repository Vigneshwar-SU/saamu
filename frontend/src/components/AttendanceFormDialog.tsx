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
import {
  ATTENDANCE_STATUS_LABELS,
  ATTENDANCE_STATUSES,
} from '../types/attendance';
import type {
  Attendance,
  AttendancePayload,
  AttendanceStatus,
} from '../types/attendance';

const attendanceSchema = z.object({
  tailor: z.number({ required_error: 'Select a tailor' }).positive('Select a tailor'),
  attendance_date: z.string().min(1, 'Attendance date is required'),
  status: z.enum(ATTENDANCE_STATUSES, { required_error: 'Select a status' }),
  notes: z.string().max(2000, 'Notes must be 2000 characters or fewer'),
});

type AttendanceFormData = z.infer<typeof attendanceSchema>;

interface AttendanceFormDialogProps {
  open: boolean;
  initial: Attendance | null;
  onClose: () => void;
  submit: (payload: AttendancePayload) => Promise<unknown>;
  defaultTailorId?: number;
}

export const AttendanceFormDialog: React.FC<AttendanceFormDialogProps> = ({
  open,
  initial,
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
  } = useForm<AttendanceFormData>({
    resolver: zodResolver(attendanceSchema),
    defaultValues: {
      tailor: 0,
      attendance_date: dayjs().format('YYYY-MM-DD'),
      status: 'PRESENT',
      notes: '',
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        tailor: initial?.tailor.id ?? defaultTailorId ?? 0,
        attendance_date: initial?.attendance_date ?? dayjs().format('YYYY-MM-DD'),
        status: initial?.status ?? 'PRESENT',
        notes: initial?.notes ?? '',
      });
      setSubmitError(null);
    }
  }, [open, initial, defaultTailorId, reset]);

  const onSubmit = async (data: AttendanceFormData) => {
    setSubmitError(null);
    try {
      await submit({
        tailor: data.tailor,
        attendance_date: data.attendance_date,
        status: data.status as AttendanceStatus,
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
        {initial ? 'Edit Attendance' : 'Mark Attendance'}
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
                  disabled={!!initial}
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
            name="attendance_date"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Attendance Date *"
                type="date"
                fullWidth
                size="small"
                InputLabelProps={{ shrink: true }}
                error={!!errors.attendance_date}
                helperText={errors.attendance_date?.message}
              />
            )}
          />

          <Controller
            name="status"
            control={control}
            render={({ field }) => (
              <FormControl fullWidth size="small" error={!!errors.status}>
                <InputLabel>Status *</InputLabel>
                <Select
                  {...field}
                  label="Status *"
                  value={field.value}
                  onChange={(event) => field.onChange(event.target.value)}
                >
                  {ATTENDANCE_STATUSES.map((status) => (
                    <MenuItem key={status} value={status}>
                      {ATTENDANCE_STATUS_LABELS[status]}
                    </MenuItem>
                  ))}
                </Select>
                {errors.status && <FormHelperText>{errors.status.message}</FormHelperText>}
              </FormControl>
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
          {initial ? 'Save Changes' : 'Save Attendance'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
