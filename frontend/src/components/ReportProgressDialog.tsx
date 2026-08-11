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
  Typography,
} from '@mui/material';
import { getApiErrorMessage } from '../utils/apiErrors';
import type { WorkAssignment } from '../types/tailors';

interface ReportProgressDialogProps {
  open: boolean;
  assignment: WorkAssignment | null;
  onClose: () => void;
  submit: (completedQuantity: number) => Promise<unknown>;
}

const ReportProgressDialog: React.FC<ReportProgressDialogProps> = ({ open, assignment, onClose, submit }) => {
  const [value, setValue] = useState('');
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (open && assignment) {
      setValue(String(assignment.completed_quantity));
      setSubmitError(null);
    }
  }, [open, assignment]);

  if (!assignment) return null;

  const max = assignment.assigned_quantity;

  const handleSubmit = async () => {
    const quantity = Number(value);
    if (!Number.isInteger(quantity) || quantity < 0 || quantity > max) {
      setSubmitError(`Completed quantity must be between 0 and ${max}.`);
      return;
    }
    setSubmitError(null);
    setIsSubmitting(true);
    try {
      await submit(quantity);
      onClose();
    } catch (error) {
      setSubmitError(getApiErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle sx={{ fontWeight: 700 }}>Report Progress</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5} sx={{ mt: 0.5 }}>
          {submitError && <Alert severity="error">{submitError}</Alert>}
          <Typography variant="body2" sx={{ color: '#6B6B6B' }}>
            {assignment.order_item.garment_type} · assigned {assignment.assigned_quantity} pcs
          </Typography>
          <TextField
            label="Completed quantity"
            type="number"
            value={value}
            onChange={(event) => setValue(event.target.value)}
            inputProps={{ min: 0, max }}
            fullWidth
            autoFocus
          />
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} color="inherit">
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={isSubmitting}
          startIcon={isSubmitting ? <CircularProgress size={16} color="inherit" /> : undefined}
          
        >
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ReportProgressDialog;
