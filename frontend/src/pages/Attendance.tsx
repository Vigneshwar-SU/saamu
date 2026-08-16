import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import EventNoteIcon from '@mui/icons-material/EventNote';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import EditIcon from '@mui/icons-material/Edit';
import { useAuth } from '../context/useAuth';
import { formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { AttendanceFormDialog } from '../components/AttendanceFormDialog';
import { PageHeader } from '../components/ui/PageHeader';
import { FilterBar } from '../components/ui/FilterBar';
import { ResponsiveTable } from '../components/ui/ResponsiveTable';
import { AppPagination } from '../components/ui/AppPagination';
import { StatusBadge } from '../components/ui/StatusBadge';
import type { StatusTone } from '../components/ui/StatusBadge';
import {
  useCreateAttendance,
  useAttendanceList,
  useUpdateAttendance,
} from '../hooks/useAttendance';
import { useTailorList } from '../hooks/useTailors';
import { ATTENDANCE_STATUS_LABELS, ATTENDANCE_STATUSES } from '../types/attendance';
import type { Attendance, AttendancePayload, AttendanceStatus } from '../types/attendance';

const PAGE_SIZE = 6;

const ATTENDANCE_STATUS_TONES: Record<AttendanceStatus, StatusTone> = {
  PRESENT: 'success',
  ABSENT: 'error',
  HALF_DAY: 'warning',
};

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

  const { data: tailorsData } = useTailorList({ scope: 'all', page_size: 100 });
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
      <PageHeader
        title="Attendance"
        subtitle="Mark daily tailor attendance and review records."
        icon={<FactCheckIcon />}
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Attendance' }]}
        actions={
          isStaff && (
            <Button variant="contained" startIcon={<EventNoteIcon />} onClick={openCreateDialog}>
              Mark Attendance
            </Button>
          )
        }
      />

      <FilterBar>
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
      </FilterBar>

      <ResponsiveTable
        data={data?.results ?? []}
        rowKey={(record) => record.id}
        loading={isLoading}
        refetching={isFetching && !isLoading}
        error={isError}
        errorMessage={getApiErrorMessage(error)}
        onRetry={() => refetch()}
        emptyTitle="No attendance records found"
        columns={[
          {
            label: 'Tailor',
            primary: true,
            render: (record) => (
              <Box>
                <Typography sx={{ fontWeight: 600 }}>{record.tailor.name}</Typography>
                <Typography variant="caption" sx={{ color: 'text.disabled' }}>
                  #{record.tailor.id}
                </Typography>
              </Box>
            ),
          },
          {
            label: 'Date',
            render: (record) => (
              <Typography variant="body2">{formatDate(record.attendance_date)}</Typography>
            ),
          },
          {
            label: 'Status',
            render: (record) => (
              <StatusBadge
                label={ATTENDANCE_STATUS_LABELS[record.status]}
                tone={ATTENDANCE_STATUS_TONES[record.status]}
              />
            ),
          },
          {
            label: 'Notes',
            render: (record) => <Typography variant="body2">{record.notes || '-'}</Typography>,
          },
          {
            label: 'Marked By',
            render: (record) => (
              <Typography variant="body2">{record.marked_by_name || '-'}</Typography>
            ),
          },
        ]}
        actions={
          isStaff
            ? (record) => (
                <Tooltip title="Edit record">
                  <Button
                    size="small"
                    startIcon={<EditIcon fontSize="small" />}
                    onClick={() => openEditDialog(record)}
                  >
                    Edit
                  </Button>
                </Tooltip>
              )
            : undefined
        }
      />

      {data && data.count > 0 && (
        <AppPagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />
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
