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
  IconButton,
  Paper,
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
import type { PieceRate } from '../types/tailors';

interface PieceRateDialogProps {
  open: boolean;
  onClose: () => void;
}

export const PieceRateDialog: React.FC<PieceRateDialogProps> = ({ open, onClose }) => {
  const { data, isLoading, isError, error, refetch } = usePieceRates();
  const createMutation = useCreatePieceRate();
  const updateMutation = useUpdatePieceRate();

  const [garment, setGarment] = useState('');
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
    const garmentValue = garment.trim().toUpperCase();
    const rateValue = Number(rate);
    if (!garmentValue) {
      setActionError('Garment type is required.');
      return;
    }
    if (!Number.isFinite(rateValue) || rateValue < 0) {
      setActionError('Enter a valid non-negative piece rate.');
      return;
    }
    setActionLoading(true);
    try {
      await createMutation.mutateAsync({
        garment_type: garmentValue,
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
      await updateMutation.mutateAsync({ id: pieceRate.id, payload: { rate_per_piece: rateValue } });
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

          <Paper variant="outlined" sx={{ p: 2, borderRadius: '10px', backgroundColor: '#F8FAFC' }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1.5 }}>
              Configure rate per garment type
            </Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
              <TextField
                label="Garment Type"
                placeholder="e.g. SHIRT"
                value={garment}
                onChange={(event) => setGarment(event.target.value)}
                size="small"
                fullWidth
              />
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
                startIcon={actionLoading ? <CircularProgress size={16} color="inherit" /> : <AddIcon />}
                onClick={handleAdd}
                disabled={actionLoading}
                sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' }, minWidth: 120 }}
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
            <Typography sx={{ color: '#64748B', textAlign: 'center', py: 3 }}>
              No piece rates configured yet.
            </Typography>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ backgroundColor: '#F8FAFC' }}>
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
                      <TableCell sx={{ fontWeight: 600 }}>{pieceRate.garment_type}</TableCell>
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
                            backgroundColor: pieceRate.is_active ? '#DCFCE7' : '#F1F5F9',
                            color: pieceRate.is_active ? '#15803D' : '#475569',
                          }}
                        />
                      </TableCell>
                      <TableCell align="right">
                        {editingId === pieceRate.id ? (
                          <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                            <Button size="small" color="primary" onClick={() => saveEdit(pieceRate)}>
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
                            <Tooltip title={pieceRate.is_active ? 'Deactivate rate' : 'Activate rate'}>
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
