import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  CircularProgress,
  FormControl,
  InputAdornment,
  InputLabel,
  LinearProgress,
  Link,
  MenuItem,
  Pagination,
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
import SearchIcon from '@mui/icons-material/Search';
import EditIcon from '@mui/icons-material/Edit';
import VisibilityIcon from '@mui/icons-material/Visibility';
import ArchiveIcon from '@mui/icons-material/Archive';
import UnarchiveIcon from '@mui/icons-material/Unarchive';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import GroupsIcon from '@mui/icons-material/Groups';
import PersonAddAltIcon from '@mui/icons-material/PersonAddAlt';
import TuneIcon from '@mui/icons-material/Tune';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatCurrency, formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { TailorFormDialog } from '../components/TailorFormDialog';
import { PieceRateDialog } from '../components/PieceRateDialog';
import {
  useArchiveTailor,
  useCreateTailor,
  useRestoreTailor,
  useTailorEarningsSummary,
  useTailorList,
  useUpdateTailor,
} from '../hooks/useTailors';
import type { Tailor, TailorPayload, TailorScope } from '../types/tailors';

const PAGE_SIZE = 20;

export const Tailors: React.FC = () => {
  const navigate = useNavigate();
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [scope, setScope] = useState<TailorScope>('active');
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTailor, setEditingTailor] = useState<Tailor | null>(null);
  const [pieceRateDialogOpen, setPieceRateDialogOpen] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    setPage(1);
  }, [search, scope]);

  const { data, isLoading, isError, error, isFetching, refetch } = useTailorList({ search, scope, page });
  const { data: earningsSummary } = useTailorEarningsSummary();

  const createMutation = useCreateTailor();
  const updateMutation = useUpdateTailor(editingTailor?.id ?? 0);
  const archiveMutation = useArchiveTailor();
  const restoreMutation = useRestoreTailor();

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  const openCreateDialog = () => {
    setEditingTailor(null);
    setDialogOpen(true);
  };

  const openEditDialog = (tailor: Tailor) => {
    setEditingTailor(tailor);
    setDialogOpen(true);
  };

  const closeDialog = () => {
    setDialogOpen(false);
    setEditingTailor(null);
  };

  const handleSubmit = (payload: TailorPayload) => {
    if (editingTailor) {
      return updateMutation.mutateAsync(payload);
    }
    return createMutation.mutateAsync(payload);
  };

  const handleArchive = async (tailor: Tailor) => {
    const confirmed = window.confirm(
      `Archive tailor "${tailor.name}"? The profile and work history are kept and can be restored later.`
    );
    if (!confirmed) return;
    try {
      await archiveMutation.mutateAsync(tailor.id);
    } catch (archiveError) {
      window.alert(getApiErrorMessage(archiveError));
    }
  };

  const handleRestore = async (tailor: Tailor) => {
    try {
      await restoreMutation.mutateAsync(tailor.id);
    } catch (restoreError) {
      window.alert(getApiErrorMessage(restoreError));
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
        <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
          Saamu Tailors ERP
        </Link>
        <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
          Tailors
        </Typography>
      </Breadcrumbs>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: '12px',
              backgroundColor: '#EFF6FF',
              color: '#1E3A8A',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <GroupsIcon />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              Tailors
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              Manage tailors, assign work, and track piece-rate earnings.
            </Typography>
          </Box>
        </Box>
        {isStaff && (
          <Stack direction="row" spacing={1.5}>
            <Button
              variant="outlined"
              startIcon={<TuneIcon />}
              onClick={() => setPieceRateDialogOpen(true)}
              sx={{ borderColor: '#1E3A8A', color: '#1E3A8A' }}
            >
              Piece Rates
            </Button>
            <Button
              variant="contained"
              startIcon={<PersonAddAltIcon />}
              onClick={openCreateDialog}
              sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
            >
              Add Tailor
            </Button>
          </Stack>
        )}
      </Box>

      {earningsSummary && (
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <Paper sx={{ flex: 1, p: 2, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
              TAILORS
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 700, mt: 0.5 }}>
              {earningsSummary.tailors.length}
            </Typography>
          </Paper>
          <Paper sx={{ flex: 1, p: 2, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
              PIECES COMPLETED
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 700, mt: 0.5 }}>
              {earningsSummary.summary.total_completed_quantity}
            </Typography>
          </Paper>
          <Paper sx={{ flex: 1, p: 2, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
              TOTAL EARNED
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 700, mt: 0.5, color: '#15803D' }}>
              {formatCurrency(earningsSummary.summary.total_earned)}
            </Typography>
          </Paper>
        </Stack>
      )}

      <Paper sx={{ p: 2, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search by name or mobile"
            fullWidth
            size="small"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ color: '#64748B' }} />
                </InputAdornment>
              ),
            }}
          />
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel>Scope</InputLabel>
            <Select
              value={scope}
              label="Scope"
              onChange={(event) => setScope(event.target.value as TailorScope)}
            >
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="archived">Archived</MenuItem>
              <MenuItem value="all">All</MenuItem>
            </Select>
          </FormControl>
        </Stack>
      </Paper>

      <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        {isFetching && !isLoading && <LinearProgress sx={{ height: 3 }} />}
        <TableContainer>
          <Table size="medium">
            <TableHead>
              <TableRow sx={{ backgroundColor: '#F8FAFC' }}>
                <TableCell sx={{ fontWeight: 700 }}>Tailor</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Mobile</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Outstanding</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Earned</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Created</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  Actions
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 6 }}>
                    <CircularProgress size={28} />
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <Alert severity="error" sx={{ display: 'inline-flex' }}>
                      {getApiErrorMessage(error)}
                    </Alert>
                    <Box sx={{ mt: 1.5 }}>
                      <Button size="small" variant="outlined" onClick={() => refetch()}>
                        Retry
                      </Button>
                    </Box>
                  </TableCell>
                </TableRow>
              ) : data && data.results.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 6 }}>
                    <Typography sx={{ color: '#64748B' }}>No tailors found.</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                data?.results.map((tailor) => {
                  const entry = earningsSummary?.tailors.find((summaryEntry) => summaryEntry.id === tailor.id);
                  return (
                    <TableRow
                      key={tailor.id}
                      hover
                      sx={{ cursor: 'pointer', '&:last-child td, &:last-child th': { border: 0 } }}
                      onClick={() => navigate(`/tailors/${tailor.id}`)}
                    >
                      <TableCell>
                        <Typography sx={{ fontWeight: 600 }}>{tailor.name}</Typography>
                        <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                          #{tailor.id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{tailor.mobile_number || '-'}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {entry ? `${entry.outstanding_quantity} pcs` : '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 600, color: '#15803D' }}>
                          {entry ? formatCurrency(entry.earned_amount) : '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={tailor.is_active ? 'Active' : 'Archived'}
                          size="small"
                          sx={{
                            fontWeight: 600,
                            backgroundColor: tailor.is_active ? '#DCFCE7' : '#F1F5F9',
                            color: tailor.is_active ? '#15803D' : '#64748B',
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{formatDate(tailor.created_at)}</Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                          <Tooltip title="View details">
                            <Button
                              size="small"
                              startIcon={<VisibilityIcon fontSize="small" />}
                              onClick={(event) => {
                                event.stopPropagation();
                                navigate(`/tailors/${tailor.id}`);
                              }}
                            >
                              View
                            </Button>
                          </Tooltip>
                          {isStaff && (
                            <Tooltip title={tailor.is_active ? 'Edit tailor' : 'Restore tailor'}>
                              <Button
                                size="small"
                                startIcon={
                                  tailor.is_active ? (
                                    <EditIcon fontSize="small" />
                                  ) : (
                                    <UnarchiveIcon fontSize="small" />
                                  )
                                }
                                onClick={(event) => {
                                  event.stopPropagation();
                                  if (tailor.is_active) {
                                    openEditDialog(tailor);
                                  } else {
                                    handleRestore(tailor);
                                  }
                                }}
                              >
                                {tailor.is_active ? 'Edit' : 'Restore'}
                              </Button>
                            </Tooltip>
                          )}
                          {isStaff && tailor.is_active && (
                            <Tooltip title="Archive tailor">
                              <Button
                                size="small"
                                color="error"
                                startIcon={<ArchiveIcon fontSize="small" />}
                                onClick={(event) => {
                                  event.stopPropagation();
                                  handleArchive(tailor);
                                }}
                              >
                                Archive
                              </Button>
                            </Tooltip>
                          )}
                        </Stack>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {data && data.count > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" sx={{ color: '#64748B' }}>
            Showing {data.results.length} of {data.count} tailors
          </Typography>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(_event, value) => setPage(value)}
            color="primary"
          />
        </Box>
      )}

      <TailorFormDialog open={dialogOpen} initial={editingTailor} onClose={closeDialog} submit={handleSubmit} />
      <PieceRateDialog open={pieceRateDialogOpen} onClose={() => setPieceRateDialogOpen(false)} />
    </Box>
  );
};
