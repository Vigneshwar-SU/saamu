import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  CircularProgress,
  FormControl,
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
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import EventNoteIcon from '@mui/icons-material/EventNote';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import EditIcon from '@mui/icons-material/Edit';
import { useAuth } from '../context/useAuth';
import { formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { AttendanceFormDialog } from '../components/AttendanceFormDialog';
import { useCreateAttendance, useAttendanceList, useUpdateAttendance } from '../hooks/useAttendance';
import { useTailorList } from '../hooks/useTailors';
import {
  ATTENDANCE_STATUS_COLORS,
  ATTENDANCE_STATUS_LABELS,
  ATTENDANCE_STATUSES,
} from '../types/attendance';
import type { Attendance, AttendancePayload, AttendanceStatus } from '../types/attendance';

const PAGE_SIZE = 20;

export const AttendancePage: React.FC = () => {
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [tailorFilter, setTailorFilter] = useState<number | ''>('');
  const [statusFilter, setStatusFilter] = useState<AttendanceStatus | ''>('');
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState<Attendance | null>(null);

  const { data: tailorsData } = useTailorList({ scope: 'all' });
  const tailors = tailorsData?.results ?? [];

  useEffect(() => {
    setPage(1);
  }, [dateFrom, dateTo, tailorFilter, statusFilter]);

  const { data, isLoading, isError, error, isFetching, refetch } = useAttendanceList({
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    tailor: tailorFilter === '' ? undefined : tailorFilter,
    status: statusFilter || undefined,
    page,
  });

  const createMutation = useCreateAttendance();
  const updateMutation = useUpdateAttendance();

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  const openCreateDialog = () => {
    setEditingRecord(null);
    setDialogOpen(true);
  };

  const openEditDialog = (record: Attendance) => {
    setEditingRecord(record);
    setDialogOpen(true);
  };

  const closeDialog = () => {
    setDialogOpen(false);
    setEditingRecord(null);
  };

  const handleSubmit = (payload: AttendancePayload) => {
    if (editingRecord) {
      return updateMutation.mutateAsync({ id: editingRecord.id, payload });
    }
    return createMutation.mutateAsync(payload);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
        <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
          Saamu Tailors ERP
        </Link>
        <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
          Attendance
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
            <FactCheckIcon />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              Attendance
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              Mark daily tailor attendance and review records.
            </Typography>
          </Box>
        </Box>
        {isStaff && (
          <Button
            variant="contained"
            startIcon={<EventNoteIcon />}
            onClick={openCreateDialog}
            sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
          >
            Mark Attendance
          </Button>
        )}
      </Box>

      <Paper sx={{ p: 2, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField
            label="From"
            type="date"
            value={dateFrom}
            onChange={(event) => setDateFrom(event.target.value)}
            size="small"
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="To"
            type="date"
            value={dateTo}
            onChange={(event) => setDateTo(event.target.value)}
            size="small"
            InputLabelProps={{ shrink: true }}
          />
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel>Tailor</InputLabel>
            <Select
              value={tailorFilter}
              label="Tailor"
              onChange={(event) => setTailorFilter(event.target.value as number | '')}
            >
              <MenuItem value="">All tailors</MenuItem>
              {tailors.map((tailor) => (
                <MenuItem key={tailor.id} value={tailor.id}>
                  {tailor.name}
                  {tailor.is_active ? '' : ' (Archived)'}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              label="Status"
              onChange={(event) => setStatusFilter(event.target.value as AttendanceStatus | '')}
            >
              <MenuItem value="">All statuses</MenuItem>
              {ATTENDANCE_STATUSES.map((status) => (
                <MenuItem key={status} value={status}>
                  {ATTENDANCE_STATUS_LABELS[status]}
                </MenuItem>
              ))}
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
                <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Notes</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Marked By</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  Actions
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                    <CircularProgress size={28} />
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
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
                  <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                    <Typography sx={{ color: '#64748B' }}>No attendance records found.</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                data?.results.map((record) => {
                  const colors = ATTENDANCE_STATUS_COLORS[record.status];
                  return (
                    <TableRow key={record.id} hover sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                      <TableCell>
                        <Typography sx={{ fontWeight: 600 }}>{record.tailor.name}</Typography>
                        <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                          #{record.tailor.id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{formatDate(record.attendance_date)}</Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={ATTENDANCE_STATUS_LABELS[record.status]}
                          size="small"
                          sx={{ fontWeight: 600, backgroundColor: colors.bg, color: colors.text }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 260 }}>
                          {record.notes || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{record.marked_by_name || '-'}</Typography>
                      </TableCell>
                      <TableCell align="right">
                        {isStaff && (
                          <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                            <Tooltip title="Edit record">
                              <Button
                                size="small"
                                startIcon={<EditIcon fontSize="small" />}
                                onClick={() => openEditDialog(record)}
                              >
                                Edit
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

      {data && data.count > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" sx={{ color: '#64748B' }}>
            Showing {data.results.length} of {data.count} records
          </Typography>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(_event, value) => setPage(value)}
            color="primary"
          />
        </Box>
      )}

      <AttendanceFormDialog
        open={dialogOpen}
        initial={editingRecord}
        onClose={closeDialog}
        submit={handleSubmit}
      />
    </Box>
  );
};
