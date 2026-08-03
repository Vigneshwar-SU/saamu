import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Breadcrumbs,
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
  Link,
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
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
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
import {
  NEXT_ASSIGNMENT_STATUS,
  WORK_ASSIGNMENT_STATUS_COLORS,
  WORK_ASSIGNMENT_STATUS_LABELS,
} from '../types/tailors';
import type {
  TailorPayload,
  WorkAssignment,
  WorkAssignmentStatus,
} from '../types/tailors';

const InfoCell: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string;
}> = ({ icon, label, value }) => (
  <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
    <Box
      sx={{
        width: 36,
        height: 36,
        borderRadius: '10px',
        backgroundColor: '#F1F5F9',
        color: '#475569',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}
    >
      {icon}
    </Box>
    <Box>
      <Typography
        variant="caption"
        sx={{ color: '#94A3B8', textTransform: 'uppercase', fontSize: '0.68rem', fontWeight: 600 }}
      >
        {label}
      </Typography>
      <Typography variant="body2" sx={{ fontWeight: 500, color: '#0F172A', whiteSpace: 'pre-wrap' }}>
        {value}
      </Typography>
    </Box>
  </Box>
);

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
          <Typography variant="body2" sx={{ color: '#475569' }}>
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
          sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
        >
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const statusChip = (status: WorkAssignmentStatus) => {
  const colors = WORK_ASSIGNMENT_STATUS_COLORS[status];
  return (
    <Chip
      label={WORK_ASSIGNMENT_STATUS_LABELS[status]}
      size="small"
      sx={{ fontWeight: 600, backgroundColor: colors.bg, color: colors.text }}
    />
  );
};

export const TailorDetail: React.FC = () => {
  const { id } = useParams();
  const tailorId = Number(id);
  const navigate = useNavigate();
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const { data: tailor, isLoading, isError, error, refetch } = useTailor(tailorId);
  const { data: earnings } = useTailorEarnings(tailorId);

  const [statusFilter, setStatusFilter] = useState<WorkAssignmentStatus | ''>('');
  const { data: assignmentsData } = useWorkAssignmentList({ tailor: tailorId, status: statusFilter });

  const updateMutation = useUpdateTailor(tailorId);
  const archiveMutation = useArchiveTailor();
  const restoreMutation = useRestoreTailor();
  const statusMutation = useChangeWorkAssignmentStatus();
  const progressMutation = useUpdateWorkAssignment();

  const [editOpen, setEditOpen] = useState(false);
  const [assignOpen, setAssignOpen] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState<WorkAssignment | null>(null);
  const [progressOpen, setProgressOpen] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const assignments = useMemo(() => assignmentsData?.results ?? [], [assignmentsData]);

  const handleArchive = async () => {
    if (!tailor) return;
    const confirmed = window.confirm(
      `Archive tailor "${tailor.name}"? The profile and work history are kept and can be restored later.`
    );
    if (!confirmed) return;
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
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !tailor) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, py: 8 }}>
        <Alert severity="error">{getApiErrorMessage(error)}</Alert>
        <Button variant="outlined" onClick={() => refetch()}>
          Retry
        </Button>
        <Button color="inherit" onClick={() => navigate('/tailors')}>
          Back to Tailors
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
        <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
          Saamu Tailors ERP
        </Link>
        <Link underline="hover" color="inherit" href="/tailors" sx={{ fontSize: '0.85rem' }}>
          Tailors
        </Link>
        <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
          {tailor.name}
        </Typography>
      </Breadcrumbs>

      {actionError && <Alert severity="error">{actionError}</Alert>}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 2 }}>
        <Stack direction="row" spacing={1.5} alignItems="flex-start">
          <Tooltip title="Back to tailors">
            <IconButton
              onClick={() => navigate('/tailors')}
              sx={{ border: '1px solid #E2E8F0', borderRadius: '10px', color: '#475569' }}
            >
              <ArrowBackIcon />
            </IconButton>
          </Tooltip>
          <Box>
            <Stack direction="row" spacing={1} alignItems="center">
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {tailor.name}
              </Typography>
              <Chip
                label={tailor.is_active ? 'Active' : 'Archived'}
                size="small"
                sx={{
                  fontWeight: 600,
                  backgroundColor: tailor.is_active ? '#DCFCE7' : '#F1F5F9',
                  color: tailor.is_active ? '#15803D' : '#475569',
                }}
              />
            </Stack>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              Tailor #{tailor.id} · Joined {formatDate(tailor.created_at)}
            </Typography>
          </Box>
        </Stack>

        {isStaff && (
          <Stack direction="row" spacing={1}>
            {tailor.is_active ? (
              <>
                <Button variant="outlined" startIcon={<EditIcon />} onClick={() => setEditOpen(true)}>
                  Edit
                </Button>
                <Button
                  variant="contained"
                  startIcon={<PersonAddAltIcon />}
                  onClick={() => setAssignOpen(true)}
                  sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
                >
                  Assign Work
                </Button>
                <Button variant="outlined" color="error" startIcon={<ArchiveIcon />} onClick={handleArchive}>
                  Archive
                </Button>
              </>
            ) : (
              <Button variant="outlined" startIcon={<UnarchiveIcon />} onClick={handleRestore}>
                Restore
              </Button>
            )}
          </Stack>
        )}
      </Box>

      <Paper sx={{ p: 3, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 2.5 }}>
          Profile
        </Typography>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
            gap: 3,
          }}
        >
          <InfoCell
            icon={<StraightenIcon sx={{ fontSize: 18 }} />}
            label="Mobile Number"
            value={tailor.mobile_number || '-'}
          />
          <InfoCell
            icon={<PaymentsIcon sx={{ fontSize: 18 }} />}
            label="Active"
            value={tailor.is_active ? 'Yes' : 'No'}
          />
          <InfoCell icon={<EditIcon sx={{ fontSize: 18 }} />} label="Notes" value={tailor.notes || '-'} />
        </Box>
      </Paper>

      {earnings && (
        <Paper sx={{ p: 3, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 2.5 }}>
            Workload &amp; Earnings
          </Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
              gap: 3,
            }}
          >
            <InfoCell
              icon={<StraightenIcon sx={{ fontSize: 18 }} />}
              label="Total Assigned"
              value={formatPieces(earnings.workload.assigned_quantity)}
            />
            <InfoCell
              icon={<CheckCircleIcon sx={{ fontSize: 18 }} />}
              label="Total Completed"
              value={formatPieces(earnings.workload.completed_quantity)}
            />
            <InfoCell
              icon={<PaymentsIcon sx={{ fontSize: 18 }} />}
              label="Total Outstanding"
              value={formatPieces(earnings.workload.outstanding_quantity)}
            />
            <InfoCell
              icon={<PaymentsIcon sx={{ fontSize: 18 }} />}
              label="Total Earned"
              value={formatCurrency(earnings.workload.earned_amount)}
            />
          </Box>
          {earnings.garment_breakdown.length > 0 && (
            <Box sx={{ mt: 2.5 }}>
              <Typography
                variant="caption"
                sx={{ color: '#94A3B8', textTransform: 'uppercase', fontSize: '0.68rem', fontWeight: 600 }}
              >
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
                      border: '1px solid #E2E8F0',
                      backgroundColor: '#F8FAFC',
                    }}
                  >
                    <Typography sx={{ fontWeight: 600, color: '#0F172A' }}>
                      {entry.garment_type}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#64748B' }}>
                      {formatPieces(entry.completed_quantity)} · {formatCurrency(entry.earned_amount)}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Box>
          )}
        </Paper>
      )}

      <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        <Box sx={{ px: 3, py: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2 }}>
          <Stack direction="row" spacing={1} alignItems="center">
            <Box
              sx={{
                width: 40,
                height: 40,
                borderRadius: '10px',
                backgroundColor: '#EFF6FF',
                color: '#1E3A8A',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <PersonAddAltIcon fontSize="small" />
            </Box>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                Work Assignments
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B' }}>
                Piece-rate work assigned to this tailor
              </Typography>
            </Box>
          </Stack>
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
        </Box>
        <TableContainer>
          <Table size="medium">
            <TableHead>
              <TableRow sx={{ backgroundColor: '#F8FAFC' }}>
                <TableCell sx={{ fontWeight: 700 }}>Order</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Garment</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>
                  Assigned
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>
                  Completed
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>
                  Outstanding
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  Rate
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  Earned
                </TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  Actions
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {assignments.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center" sx={{ py: 6 }}>
                    <Typography sx={{ color: '#64748B' }}>
                      {statusFilter ? 'No assignments match this status.' : 'No work assigned yet.'}
                    </Typography>
                  </TableCell>
                </TableRow>
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
                        <Typography sx={{ fontWeight: 600 }}>{assignment.order_item.garment_type}</Typography>
                        <Typography variant="caption" sx={{ color: '#94A3B8' }}>
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
                        <Typography variant="body2" sx={{ fontWeight: 600, color: '#B45309' }}>
                          {formatPieces(assignment.assigned_quantity - assignment.completed_quantity)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">{formatCurrency(assignment.rate_per_piece_snapshot)}</Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" sx={{ fontWeight: 600, color: '#15803D' }}>
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
                                {nextStatus === 'COMPLETED' ? 'Complete' : WORK_ASSIGNMENT_STATUS_LABELS[nextStatus]}
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
        </TableContainer>
      </Paper>

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
    </Box>
  );
};
