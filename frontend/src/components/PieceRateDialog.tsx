import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import BlockIcon from '@mui/icons-material/Block';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { getApiErrorMessage } from '../utils/apiErrors';
import { useCreatePieceRate, usePieceRates, useUpdatePieceRate } from '../hooks/useTailors';
import { formatCurrency } from '../utils/formatters';
import { PIECE_RATE_KEYS, PIECE_RATE_LABELS } from '../types/customers';
import type { PieceRateKey } from '../types/customers';
import type { PieceRate } from '../types/tailors';

interface PieceRateDialogProps {
  open: boolean;
  onClose: () => void;
}

/**
 * Full Shirt and Half Shirt are paid separately, so each variant gets its own
 * rate. The key is a fixed, closed set: it is the join key an order line
 * resolves to, so it must never be typed freely.
 */
const RATE_OPTIONS: Array<{ key: PieceRateKey; label: string }> = PIECE_RATE_KEYS.map((key) => ({
  key,
  label: PIECE_RATE_LABELS[key],
}));

export const PieceRateDialog: React.FC<PieceRateDialogProps> = ({ open, onClose }) => {
  const { data, isLoading, isError, error, refetch } = usePieceRates();
  const createMutation = useCreatePieceRate();
  const updateMutation = useUpdatePieceRate();

  const [garment, setGarment] = useState<PieceRateKey | ''>('');
  const [rate, setRate] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editRate, setEditRate] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (open) {
      setActionError(null);
      setGarment('');
      setRate('');
      setEditingId(null);
    }
  }, [open]);

  const handleAdd = async () => {
    setActionError(null);
    const rateValue = Number(rate);
    if (!garment) {
      setActionError('Select a garment type.');
      return;
    }
    if (!Number.isFinite(rateValue) || rateValue < 0) {
      setActionError('Enter a valid non-negative piece rate.');
      return;
    }
    setActionLoading(true);
    try {
      await createMutation.mutateAsync({
        garment_type: garment,
        rate_per_piece: rateValue,
      });
      setGarment('');
      setRate('');
    } catch (createError) {
      setActionError(getApiErrorMessage(createError));
    } finally {
      setActionLoading(false);
    }
  };

  const startEdit = (pieceRate: PieceRate) => {
    setEditingId(pieceRate.id);
    setEditRate(String(pieceRate.rate_per_piece));
  };

  const saveEdit = async (pieceRate: PieceRate) => {
    setActionError(null);
    const rateValue = Number(editRate);
    if (!Number.isFinite(rateValue) || rateValue < 0) {
      setActionError('Enter a valid non-negative piece rate.');
      return;
    }
    setActionLoading(true);
    try {
      await updateMutation.mutateAsync({
        id: pieceRate.id,
        payload: { rate_per_piece: rateValue },
      });
      setEditingId(null);
    } catch (updateError) {
      setActionError(getApiErrorMessage(updateError));
    } finally {
      setActionLoading(false);
    }
  };

  const toggleActive = async (pieceRate: PieceRate) => {
    setActionError(null);
    setActionLoading(true);
    try {
      await updateMutation.mutateAsync({
        id: pieceRate.id,
        payload: { is_active: !pieceRate.is_active },
      });
    } catch (toggleError) {
      setActionError(getApiErrorMessage(toggleError));
    } finally {
      setActionLoading(false);
    }
  };

  const rates = data?.results ?? [];

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle sx={{ fontWeight: 700 }}>Piece Rates</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5} sx={{ mt: 0.5 }}>
          {actionError && <Alert severity="error">{actionError}</Alert>}

          <Paper variant="outlined" sx={{ p: 2, borderRadius: '10px', backgroundColor: '#FBF6EA' }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 0.5 }}>
              Configure rate per garment type
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 1.5 }}>
              Full Shirt and Half Shirt are paid separately, so each needs its own rate.
            </Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
              <FormControl size="small" fullWidth>
                <InputLabel>Garment Type</InputLabel>
                <Select
                  value={garment}
                  label="Garment Type"
                  onChange={(event) => setGarment(event.target.value as PieceRateKey | '')}
                >
                  {RATE_OPTIONS.map((option) => (
                    <MenuItem key={option.key} value={option.key}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField
                label="Rate per piece (INR)"
                placeholder="e.g. 150"
                value={rate}
                onChange={(event) => setRate(event.target.value)}
                size="small"
                type="number"
                fullWidth
              />
              <Button
                variant="contained"
                startIcon={
                  actionLoading ? <CircularProgress size={16} color="inherit" /> : <AddIcon />
                }
                onClick={handleAdd}
                disabled={actionLoading}
                sx={{ minWidth: 120 }}
              >
                Add
              </Button>
            </Stack>
          </Paper>

          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress size={24} />
            </Box>
          ) : isError ? (
            <Stack spacing={1.5} alignItems="center">
              <Alert severity="error">{getApiErrorMessage(error)}</Alert>
              <Button size="small" variant="outlined" onClick={() => refetch()}>
                Retry
              </Button>
            </Stack>
          ) : rates.length === 0 ? (
            <Typography sx={{ color: '#6B6B6B', textAlign: 'center', py: 3 }}>
              No piece rates configured yet.
            </Typography>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ backgroundColor: '#FBF6EA' }}>
                    <TableCell sx={{ fontWeight: 700 }}>Garment</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Rate / Piece</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>
                      Actions
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rates.map((pieceRate) => (
                    <TableRow key={pieceRate.id} hover>
                      <TableCell sx={{ fontWeight: 600 }}>
                        {pieceRate.garment_label || pieceRate.garment_type}
                      </TableCell>
                      <TableCell>
                        {editingId === pieceRate.id ? (
                          <TextField
                            value={editRate}
                            onChange={(event) => setEditRate(event.target.value)}
                            size="small"
                            type="number"
                            autoFocus
                            sx={{ width: 120 }}
                            onKeyDown={(event) => {
                              if (event.key === 'Enter') saveEdit(pieceRate);
                            }}
                          />
                        ) : (
                          formatCurrency(pieceRate.rate_per_piece)
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={pieceRate.is_active ? 'Active' : 'Inactive'}
                          size="small"
                          sx={{
                            fontWeight: 600,
                            backgroundColor: pieceRate.is_active ? '#E7F1EA' : '#F1EDE2',
                            color: pieceRate.is_active ? '#1F5C3C' : '#6B6B6B',
                          }}
                        />
                      </TableCell>
                      <TableCell align="right">
                        {editingId === pieceRate.id ? (
                          <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                            <Button
                              size="small"
                              color="primary"
                              onClick={() => saveEdit(pieceRate)}
                            >
                              Save
                            </Button>
                            <Button size="small" color="inherit" onClick={() => setEditingId(null)}>
                              Cancel
                            </Button>
                          </Stack>
                        ) : (
                          <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                            <Tooltip title="Edit rate">
                              <IconButton size="small" onClick={() => startEdit(pieceRate)}>
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip
                              title={pieceRate.is_active ? 'Deactivate rate' : 'Activate rate'}
                            >
                              <IconButton size="small" onClick={() => toggleActive(pieceRate)}>
                                {pieceRate.is_active ? (
                                  <BlockIcon fontSize="small" color="error" />
                                ) : (
                                  <CheckCircleIcon fontSize="small" color="success" />
                                )}
                              </IconButton>
                            </Tooltip>
                          </Stack>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} color="inherit">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default PieceRateDialog;
