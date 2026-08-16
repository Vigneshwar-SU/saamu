import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  InputAdornment,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import EditIcon from '@mui/icons-material/Edit';
import VisibilityIcon from '@mui/icons-material/Visibility';
import ArchiveIcon from '@mui/icons-material/Archive';
import UnarchiveIcon from '@mui/icons-material/Unarchive';
import GroupsIcon from '@mui/icons-material/Groups';
import PersonAddAltIcon from '@mui/icons-material/PersonAddAlt';
import TuneIcon from '@mui/icons-material/Tune';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatCurrency, formatDate, formatPieces } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { TailorFormDialog } from '../components/TailorFormDialog';
import { PieceRateDialog } from '../components/PieceRateDialog';
import { PageHeader } from '../components/ui/PageHeader';
import { FilterBar } from '../components/ui/FilterBar';
import { ResponsiveTable } from '../components/ui/ResponsiveTable';
import { AppPagination } from '../components/ui/AppPagination';
import { StatusBadge } from '../components/ui/StatusBadge';
import { StatCard } from '../components/ui/StatCard';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import {
  useArchiveTailor,
  useCreateTailor,
  useRestoreTailor,
  useTailorEarningsSummary,
  useTailorList,
  useUpdateTailor,
} from '../hooks/useTailors';
import type { Tailor, TailorPayload, TailorScope } from '../types/tailors';

const PAGE_SIZE = 6;

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
  const [archiveTarget, setArchiveTarget] = useState<Tailor | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    setPage(1);
  }, [search, scope]);

  const { data, isLoading, isError, error, isFetching, refetch } = useTailorList({
    search,
    scope,
    page,
  });
  const { data: earningsSummary } = useTailorEarningsSummary();

  const createMutation = useCreateTailor();
  const updateMutation = useUpdateTailor(editingTailor?.id ?? 0);
  const archiveMutation = useArchiveTailor();
  const restoreMutation = useRestoreTailor();

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

  const confirmArchive = async () => {
    if (!archiveTarget) return;
    try {
      await archiveMutation.mutateAsync(archiveTarget.id);
    } catch (archiveError) {
      window.alert(getApiErrorMessage(archiveError));
    }
    setArchiveTarget(null);
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
      <PageHeader
        title="Tailors"
        subtitle="Manage tailors, assign work, and track piece-rate earnings."
        icon={<GroupsIcon />}
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Tailors' }]}
        actions={
          isStaff && (
            <Stack direction="row" spacing={1.5}>
              <Button
                variant="outlined"
                startIcon={<TuneIcon />}
                onClick={() => setPieceRateDialogOpen(true)}
              >
                Piece Rates
              </Button>
              <Button
                variant="contained"
                startIcon={<PersonAddAltIcon />}
                onClick={openCreateDialog}
              >
                Add Tailor
              </Button>
            </Stack>
          )
        }
      />

      {earningsSummary && (
        <Box
          sx={{
            display: 'grid',
            gap: 2,
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(5, 1fr)' },
          }}
        >
          <StatCard
            label="TOTAL TAILORS"
            value={String(
              earningsSummary.summary.total_active_tailors ?? earningsSummary.tailors.length
            )}
          />
          <StatCard
            label="TOTAL ASSIGNED"
            value={formatPieces(earningsSummary.summary.workload?.total_assigned ?? 0)}
          />
          <StatCard
            label="TOTAL COMPLETED"
            value={formatPieces(earningsSummary.summary.workload?.total_completed ?? 0)}
            tone="success"
          />
          <StatCard
            label="TOTAL OUTSTANDING"
            value={formatPieces(earningsSummary.summary.workload?.total_outstanding ?? 0)}
            tone="warning"
          />
          <StatCard
            label="TOTAL EARNED"
            value={formatCurrency(earningsSummary.summary.workload?.total_earned ?? 0)}
            tone="success"
          />
        </Box>
      )}

      <FilterBar>
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
                  <SearchIcon sx={{ color: 'text.secondary' }} />
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
      </FilterBar>

      <ResponsiveTable
        data={data?.results ?? []}
        rowKey={(tailor) => tailor.id}
        onRowClick={(tailor) => navigate(`/tailors/${tailor.id}`)}
        loading={isLoading}
        refetching={isFetching && !isLoading}
        error={isError}
        errorMessage={getApiErrorMessage(error)}
        onRetry={() => refetch()}
        emptyTitle="No tailors found"
        columns={[
          {
            label: 'Tailor',
            primary: true,
            render: (tailor) => (
              <Box>
                <Typography sx={{ fontWeight: 600 }}>{tailor.name}</Typography>
                <Typography variant="caption" sx={{ color: 'text.disabled' }}>
                  #{tailor.id}
                </Typography>
              </Box>
            ),
          },
          {
            label: 'Mobile',
            render: (tailor) => (
              <Typography variant="body2">{tailor.mobile_number || '-'}</Typography>
            ),
          },
          {
            label: 'Assigned',
            render: (tailor) => {
              const entry = earningsSummary?.tailors.find(
                (summaryEntry) => summaryEntry.id === tailor.id
              );
              const workload = entry?.workload ?? {
                assigned_quantity: 0,
                completed_quantity: 0,
                outstanding_quantity: 0,
                earned_amount: 0,
              };
              return (
                <Typography variant="body2">{formatPieces(workload.assigned_quantity)}</Typography>
              );
            },
          },
          {
            label: 'Completed',
            render: (tailor) => {
              const entry = earningsSummary?.tailors.find(
                (summaryEntry) => summaryEntry.id === tailor.id
              );
              const workload = entry?.workload ?? {
                assigned_quantity: 0,
                completed_quantity: 0,
                outstanding_quantity: 0,
                earned_amount: 0,
              };
              return (
                <Typography variant="body2">{formatPieces(workload.completed_quantity)}</Typography>
              );
            },
          },
          {
            label: 'Outstanding',
            render: (tailor) => {
              const entry = earningsSummary?.tailors.find(
                (summaryEntry) => summaryEntry.id === tailor.id
              );
              const workload = entry?.workload ?? {
                assigned_quantity: 0,
                completed_quantity: 0,
                outstanding_quantity: 0,
                earned_amount: 0,
              };
              return (
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {formatPieces(workload.outstanding_quantity)}
                </Typography>
              );
            },
          },
          {
            label: 'Earned',
            render: (tailor) => {
              const entry = earningsSummary?.tailors.find(
                (summaryEntry) => summaryEntry.id === tailor.id
              );
              const workload = entry?.workload ?? {
                assigned_quantity: 0,
                completed_quantity: 0,
                outstanding_quantity: 0,
                earned_amount: 0,
              };
              return (
                <Typography variant="body2" sx={{ fontWeight: 600, color: 'success.dark' }}>
                  {formatCurrency(workload.earned_amount)}
                </Typography>
              );
            },
          },
          {
            label: 'Status',
            render: (tailor) => (
              <StatusBadge
                label={tailor.is_active ? 'Active' : 'Archived'}
                tone={tailor.is_active ? 'success' : 'neutral'}
              />
            ),
          },
          {
            label: 'Created',
            render: (tailor) => (
              <Typography variant="body2">{formatDate(tailor.created_at)}</Typography>
            ),
          },
        ]}
        actions={(tailor) => (
          <Stack direction="row" spacing={0.5} flexWrap="wrap">
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
                    setArchiveTarget(tailor);
                  }}
                >
                  Archive
                </Button>
              </Tooltip>
            )}
          </Stack>
        )}
      />

      {data && data.count > 0 && (
        <AppPagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />
      )}

      <ConfirmDialog
        open={archiveTarget !== null}
        title="Archive tailor"
        message={
          archiveTarget
            ? `Archive tailor "${archiveTarget.name}"? The profile and work history are kept and can be restored later.`
            : ''
        }
        confirmLabel="Archive"
        tone="warning"
        loading={archiveMutation.isPending}
        onConfirm={confirmArchive}
        onCancel={() => setArchiveTarget(null)}
      />

      <TailorFormDialog
        open={dialogOpen}
        initial={editingTailor}
        onClose={closeDialog}
        submit={handleSubmit}
      />
      <PieceRateDialog open={pieceRateDialogOpen} onClose={() => setPieceRateDialogOpen(false)} />
    </Box>
  );
};
