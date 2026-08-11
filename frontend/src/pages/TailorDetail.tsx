import React, { useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import PersonAddAltIcon from '@mui/icons-material/PersonAddAlt';
import EditIcon from '@mui/icons-material/Edit';
import ArchiveIcon from '@mui/icons-material/Archive';
import UnarchiveIcon from '@mui/icons-material/Unarchive';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StraightenIcon from '@mui/icons-material/Straighten';
import PaymentsIcon from '@mui/icons-material/Payments';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatCurrency, formatDate, formatPieces } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { TailorFormDialog } from '../components/TailorFormDialog';
import AssignWorkDialog from '../components/AssignWorkDialog';
import ReportProgressDialog from '../components/ReportProgressDialog';
import WorkAssignmentStatusChip from '../components/WorkAssignmentStatusChip';
import {
  useArchiveTailor,
  useChangeWorkAssignmentStatus,
  useRestoreTailor,
  useTailor,
  useTailorEarnings,
  useUpdateTailor,
  useUpdateWorkAssignment,
  useWorkAssignmentList,
} from '../hooks/useTailors';
import { NEXT_ASSIGNMENT_STATUS, WORK_ASSIGNMENT_STATUS_LABELS } from '../types/tailors';
import type { TailorPayload, WorkAssignment, WorkAssignmentStatus } from '../types/tailors';
import { PageHeader } from '../components/ui/PageHeader';
import { SectionCard } from '../components/ui/SectionCard';
import { InfoField } from '../components/ui/InfoField';
import { StatusBadge } from '../components/ui/StatusBadge';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { ErrorState } from '../components/ui/ErrorState';
import { TableCard } from '../components/ui/TableCard';
import { TableStateRow } from '../components/ui/TableStateRow';

const statusChip = (status: WorkAssignmentStatus) => <WorkAssignmentStatusChip status={status} />;

export const TailorDetail: React.FC = () => {
  const { id } = useParams();
  const tailorId = Number(id);
  const navigate = useNavigate();
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const { data: tailor, isLoading, isError, error, refetch } = useTailor(tailorId);
  const { data: earnings } = useTailorEarnings(tailorId);

  const [statusFilter, setStatusFilter] = useState<WorkAssignmentStatus | ''>('');
  const { data: assignmentsData, isLoading: assignmentsLoading } = useWorkAssignmentList({
    tailor: tailorId,
    status: statusFilter,
  });

  const updateMutation = useUpdateTailor(tailorId);
  const archiveMutation = useArchiveTailor();
  const restoreMutation = useRestoreTailor();
  const statusMutation = useChangeWorkAssignmentStatus();
  const progressMutation = useUpdateWorkAssignment();

  const [editOpen, setEditOpen] = useState(false);
  const [assignOpen, setAssignOpen] = useState(false);
  const [archiveOpen, setArchiveOpen] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState<WorkAssignment | null>(null);
  const [progressOpen, setProgressOpen] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const assignments = useMemo(() => assignmentsData?.results ?? [], [assignmentsData]);

  const handleArchive = async () => {
    setArchiveOpen(false);
    if (!tailor) return;
    setActionError(null);
    try {
      await archiveMutation.mutateAsync(tailorId);
    } catch (archiveError) {
      setActionError(getApiErrorMessage(archiveError));
    }
  };

  const handleRestore = async () => {
    if (!tailor) return;
    setActionError(null);
    try {
      await restoreMutation.mutateAsync(tailorId);
    } catch (restoreError) {
      setActionError(getApiErrorMessage(restoreError));
    }
  };

  const handleSubmitEdit = async (payload: TailorPayload) => {
    await updateMutation.mutateAsync(payload);
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
        <Typography color="text.secondary">Loading tailor…</Typography>
      </Box>
    );
  }

  if (isError || !tailor) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, py: 8 }}>
        <ErrorState message={getApiErrorMessage(error)} onRetry={() => refetch()} />
        <Button color="inherit" onClick={() => navigate('/tailors')}>
          Back to Tailors
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {actionError && <Alert severity="error">{actionError}</Alert>}

      <PageHeader
        title={tailor.name}
        subtitle={`Tailor #${tailor.id} · Joined ${formatDate(tailor.created_at)}`}
        icon={<StraightenIcon />}
        backTo="/tailors"
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Tailors', to: '/tailors' }, { label: tailor.name }]}
        actions={
          isStaff && (
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {tailor.is_active ? (
                <>
                  <Button variant="outlined" startIcon={<EditIcon />} onClick={() => setEditOpen(true)}>
                    Edit
                  </Button>
                  <Button variant="contained" startIcon={<PersonAddAltIcon />} onClick={() => setAssignOpen(true)}>
                    Assign Work
                  </Button>
                  <Button variant="outlined" color="error" startIcon={<ArchiveIcon />} onClick={() => setArchiveOpen(true)}>
                    Archive
                  </Button>
                </>
              ) : (
                <Button variant="outlined" startIcon={<UnarchiveIcon />} onClick={handleRestore}>
                  Restore
                </Button>
              )}
            </Stack>
          )
        }
      />

      <SectionCard title="Profile" icon={<StraightenIcon />}>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
            gap: 3,
          }}
        >
          <InfoField label="Status" value={<StatusBadge label={tailor.is_active ? 'Active' : 'Archived'} tone={tailor.is_active ? 'success' : 'neutral'} />} strong />
          <InfoField label="Mobile Number" value={tailor.mobile_number || '-'} />
          <InfoField label="Notes" value={tailor.notes || '-'} />
        </Box>
      </SectionCard>

      {earnings && (
        <SectionCard title="Workload & Earnings" icon={<PaymentsIcon />}>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
              gap: 3,
            }}
          >
            <InfoField label="Total Assigned" value={formatPieces(earnings.workload.assigned_quantity)} />
            <InfoField label="Total Completed" value={formatPieces(earnings.workload.completed_quantity)} />
            <InfoField label="Total Outstanding" value={formatPieces(earnings.workload.outstanding_quantity)} />
            <InfoField label="Total Earned" value={formatCurrency(earnings.workload.earned_amount)} strong />
          </Box>
          {earnings.garment_breakdown.length > 0 && (
            <Box sx={{ mt: 2.5 }}>
              <Typography variant="caption" sx={{ color: 'text.disabled', textTransform: 'uppercase', fontSize: '0.68rem', fontWeight: 600 }}>
                By Garment
              </Typography>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' },
                  gap: 2,
                  mt: 1,
                }}
              >
                {earnings.garment_breakdown.map((entry) => (
                  <Box
                    key={entry.garment_type}
                    sx={{
                      p: 1.5,
                      borderRadius: '10px',
                      border: '1px solid #E7E0D0',
                      backgroundColor: '#FBF6EA',
                    }}
                  >
                    <Typography sx={{ fontWeight: 600, color: 'text.primary' }}>
                      {entry.garment_type}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      {formatPieces(entry.completed_quantity)} · {formatCurrency(entry.earned_amount)}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Box>
          )}
        </SectionCard>
      )}

      <SectionCard
        title="Work Assignments"
        subtitle="Piece-rate work assigned to this tailor"
        icon={<PersonAddAltIcon />}
        action={
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              label="Status"
              onChange={(event) => setStatusFilter(event.target.value as WorkAssignmentStatus | '')}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="ASSIGNED">Assigned</MenuItem>
              <MenuItem value="IN_PROGRESS">In Progress</MenuItem>
              <MenuItem value="COMPLETED">Completed</MenuItem>
            </Select>
          </FormControl>
        }
        noPadding
      >
        <TableCard sx={{ border: 'none', borderRadius: 0 }}>
          <Table size="medium">
            <TableHead>
              <TableRow>
                <TableCell>Order</TableCell>
                <TableCell>Garment</TableCell>
                <TableCell align="center">Assigned</TableCell>
                <TableCell align="center">Completed</TableCell>
                <TableCell align="center">Outstanding</TableCell>
                <TableCell align="right">Rate</TableCell>
                <TableCell align="right">Earned</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {assignmentsLoading ? (
                <TableStateRow colSpan={9} state="loading" />
              ) : assignments.length === 0 ? (
                <TableStateRow
                  colSpan={9}
                  state="empty"
                  emptyTitle={statusFilter ? 'No assignments match this status' : 'No work assigned yet'}
                  emptyMessage={statusFilter ? 'Try a different status filter.' : 'Assign pieces to this tailor to get started.'}
                />
              ) : (
                assignments.map((assignment) => {
                  const nextStatus = NEXT_ASSIGNMENT_STATUS[assignment.status];
                  return (
                    <TableRow key={assignment.id} hover>
                      <TableCell>
                        <Button
                          size="small"
                          sx={{ textTransform: 'none' }}
                          onClick={() => navigate(`/orders/${assignment.order_item.order}`)}
                        >
                          {assignment.order_item.order_number}
                        </Button>
                      </TableCell>
                      <TableCell>
                        <Typography sx={{ fontWeight: 600 }}>
                          {assignment.order_item.garment_type}
                        </Typography>
                        <Typography variant="caption" sx={{ color: 'text.disabled' }}>
                          {assignment.order_item.customer_name}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2">
                          {formatPieces(assignment.assigned_quantity)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {formatPieces(assignment.completed_quantity)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2" sx={{ fontWeight: 600, color: '#8F4A00' }}>
                          {formatPieces(assignment.assigned_quantity - assignment.completed_quantity)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {formatCurrency(assignment.rate_per_piece_snapshot)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" sx={{ fontWeight: 600, color: '#1F5C3C' }}>
                          {formatCurrency(assignment.earned_amount)}
                        </Typography>
                      </TableCell>
                      <TableCell>{statusChip(assignment.status)}</TableCell>
                      <TableCell align="right">
                        {isStaff && nextStatus && (
                          <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                            <Tooltip title="Report completed quantity">
                              <Button
                                size="small"
                                startIcon={<EditIcon fontSize="small" />}
                                disabled={progressMutation.isPending}
                                onClick={() => {
                                  setSelectedAssignment(assignment);
                                  setProgressOpen(true);
                                }}
                              >
                                Progress
                              </Button>
                            </Tooltip>
                            <Tooltip title={`Move to ${WORK_ASSIGNMENT_STATUS_LABELS[nextStatus]}`}>
                              <Button
                                size="small"
                                variant="contained"
                                color={nextStatus === 'COMPLETED' ? 'success' : 'primary'}
                                disabled={statusMutation.isPending}
                                startIcon={
                                  nextStatus === 'COMPLETED' ? (
                                    <CheckCircleIcon fontSize="small" />
                                  ) : (
                                    <PlayArrowIcon fontSize="small" />
                                  )
                                }
                                onClick={async () => {
                                  setActionError(null);
                                  try {
                                    await statusMutation.mutateAsync({
                                      id: assignment.id,
                                      status: nextStatus,
                                    });
                                  } catch (transitionError) {
                                    setActionError(getApiErrorMessage(transitionError));
                                  }
                                }}
                              >
                                {nextStatus === 'COMPLETED'
                                  ? 'Complete'
                                  : WORK_ASSIGNMENT_STATUS_LABELS[nextStatus]}
                              </Button>
                            </Tooltip>
                          </Stack>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableCard>
      </SectionCard>

      <TailorFormDialog
        open={editOpen}
        initial={tailor}
        onClose={() => setEditOpen(false)}
        submit={handleSubmitEdit}
      />
      <AssignWorkDialog
        open={assignOpen}
        onClose={() => setAssignOpen(false)}
        onCreated={() => setAssignOpen(false)}
        defaultTailorId={tailorId}
      />
      <ReportProgressDialog
        open={progressOpen}
        assignment={selectedAssignment}
        onClose={() => setProgressOpen(false)}
        submit={async (completedQuantity) => {
          if (!selectedAssignment) return;
          await progressMutation.mutateAsync({
            id: selectedAssignment.id,
            completedQuantity,
          });
        }}
      />
      <ConfirmDialog
        open={archiveOpen}
        title="Archive Tailor"
        message={`Archive tailor "${tailor.name}"? The profile and work history are kept and can be restored later.`}
        confirmLabel="Archive"
        tone="error"
        loading={archiveMutation.isPending}
        onConfirm={handleArchive}
        onCancel={() => setArchiveOpen(false)}
      />
    </Box>
  );
};

export default TailorDetail;
