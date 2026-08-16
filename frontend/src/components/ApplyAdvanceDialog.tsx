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
  Paper,
  Select,
  Stack,
  Typography,
} from '@mui/material';
import { getApiErrorMessage } from '../utils/apiErrors';
import { formatCurrency, formatDate } from '../utils/formatters';
import { useAdvanceList } from '../hooks/useAdvances';
import type { AdvanceStatus } from '../types/advances';

interface ApplyAdvanceDialogProps {
  open: boolean;
  onClose: () => void;
  submit: (advanceId: number) => Promise<unknown>;
  tailorId: number;
  outstandingPayable: number;
}

export const ApplyAdvanceDialog: React.FC<ApplyAdvanceDialogProps> = ({
  open,
  onClose,
  submit,
  tailorId,
  outstandingPayable,
}) => {
  const [selectedAdvanceId, setSelectedAdvanceId] = useState<number>(0);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const { data, isLoading, isError, error, refetch } = useAdvanceList({
    tailor: tailorId,
    status: 'OUTSTANDING' as AdvanceStatus,
  });

  const eligibleAdvances = useMemo(() => data?.results ?? [], [data]);

  useEffect(() => {
    if (open) {
      setSelectedAdvanceId(0);
      setSubmitError(null);
    }
  }, [open]);

  const handleApply = async () => {
    if (!selectedAdvanceId) return;
    setSubmitError(null);
    setSubmitting(true);
    try {
      await submit(selectedAdvanceId);
      onClose();
    } catch (error) {
      setSubmitError(getApiErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle sx={{ fontWeight: 700 }}>Apply Advance</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5} sx={{ mt: 0.5 }}>
          {submitError && <Alert severity="error">{submitError}</Alert>}

          <Paper
            sx={{
              p: 2,
              borderRadius: '12px',
              border: '1px solid #E7E0D0',
              backgroundColor: '#FBF6EA',
            }}
          >
            <Typography variant="body2" sx={{ color: '#6B6B6B' }}>
              Current outstanding payable:{' '}
              <strong style={{ color: '#7A5E0C' }}>{formatCurrency(outstandingPayable)}</strong>
            </Typography>
            <Typography variant="caption" sx={{ color: '#A29B8E' }}>
              An advance reduces the outstanding payable. It cannot make the balance negative.
            </Typography>
          </Paper>

          {isLoading ? (
            <BoxLoading />
          ) : isError ? (
            <Alert severity="error">
              {getApiErrorMessage(error)}
              <Button size="small" variant="outlined" onClick={() => refetch()} sx={{ ml: 1.5 }}>
                Retry
              </Button>
            </Alert>
          ) : eligibleAdvances.length === 0 ? (
            <Alert severity="info">No outstanding advances for this tailor.</Alert>
          ) : (
            <FormControl fullWidth size="small">
              <InputLabel>Advance *</InputLabel>
              <Select
                value={selectedAdvanceId}
                label="Advance *"
                onChange={(event) => setSelectedAdvanceId(event.target.value as number)}
              >
                {eligibleAdvances.map((advance) => (
                  <MenuItem key={advance.id} value={advance.id}>
                    {formatCurrency(advance.amount)} · {formatDate(advance.advance_date)}
                    {advance.notes ? ` · ${advance.notes}` : ''}
                  </MenuItem>
                ))}
              </Select>
              {selectedAdvanceId === 0 && (
                <FormHelperText>Select an advance to apply</FormHelperText>
              )}
            </FormControl>
          )}
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
          onClick={handleApply}
          variant="contained"
          disabled={!selectedAdvanceId || submitting || isLoading}
          startIcon={submitting ? <CircularProgress size={16} color="inherit" /> : undefined}
          fullWidth
        >
          Apply Advance
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const BoxLoading: React.FC = () => (
  <Stack alignItems="center" sx={{ py: 3 }}>
    <CircularProgress size={28} />
  </Stack>
);
