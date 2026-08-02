import React, { useState } from 'react';
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  CircularProgress,
  Divider,
  IconButton,
  Link,
  Paper,
  Stack,
  Tab,
  Tabs,
  Tooltip,
  Typography,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import EditIcon from '@mui/icons-material/Edit';
import ArchiveIcon from '@mui/icons-material/Archive';
import UnarchiveIcon from '@mui/icons-material/Unarchive';
import PhoneIcon from '@mui/icons-material/Phone';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import NotesIcon from '@mui/icons-material/Notes';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import StraightenIcon from '@mui/icons-material/Straighten';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { CustomerFormDialog } from '../components/CustomerFormDialog';
import { MeasurementFormDialog } from '../components/MeasurementFormDialog';
import {
  useArchiveCustomer,
  useCustomer,
  useRestoreCustomer,
  useUpdateCustomer,
} from '../hooks/useCustomers';
import {
  useCreateMeasurement,
  useMeasurements,
  useUpdateMeasurement,
} from '../hooks/useMeasurements';
import {
  MEASUREMENT_FIELD_LABELS,
  MEASUREMENT_FIELDS_BY_GARMENT,
} from '../types/customers';
import type {
  GarmentType,
  Measurement,
  MeasurementFieldName,
  MeasurementPayload,
} from '../types/customers';

interface MeasurementDialogState {
  open: boolean;
  garment: GarmentType;
  base: Measurement | null;
}

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
      <Typography variant="caption" sx={{ color: '#94A3B8', textTransform: 'uppercase', fontSize: '0.68rem', fontWeight: 600 }}>
        {label}
      </Typography>
      <Typography variant="body2" sx={{ fontWeight: 500, color: '#0F172A', whiteSpace: 'pre-wrap' }}>
        {value}
      </Typography>
    </Box>
  </Box>
);

export const CustomerDetail: React.FC = () => {
  const { id } = useParams();
  const customerId = Number(id);
  const navigate = useNavigate();
  const { role } = useAuth();
  const isStaff = role === 'STAFF';

  const { data: customer, isLoading, isError, error, refetch } = useCustomer(customerId);
  const {
    data: measurements,
    isLoading: measurementsLoading,
    isError: measurementsError,
    refetch: refetchMeasurements,
  } = useMeasurements(customerId);

  const updateMutation = useUpdateCustomer(customerId);
  const archiveMutation = useArchiveCustomer();
  const restoreMutation = useRestoreCustomer();
  const createMeasurement = useCreateMeasurement(customerId);
  const updateMeasurement = useUpdateMeasurement(customerId);

  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [garmentTab, setGarmentTab] = useState<GarmentType>('SHIRT');
  const [measurementDialog, setMeasurementDialog] = useState<MeasurementDialogState>({
    open: false,
    garment: 'SHIRT',
    base: null,
  });

  const currentMeasurement = measurements?.find(
    (m) => m.garment_type === garmentTab && m.is_current
  );
  const historyMeasurements = (measurements ?? [])
    .filter((m) => m.garment_type === garmentTab && !m.is_current)
    .sort((a, b) => b.version - a.version);

  const openMeasurementDialog = (garment: GarmentType, base: Measurement | null) => {
    setMeasurementDialog({ open: true, garment, base });
  };

  const closeMeasurementDialog = () => {
    setMeasurementDialog((prev) => ({ ...prev, open: false }));
  };

  const handleMeasurementSubmit = (payload: MeasurementPayload) => {
    if (measurementDialog.base) {
      return updateMeasurement.mutateAsync({ id: measurementDialog.base.id, payload });
    }
    return createMeasurement.mutateAsync(payload);
  };

  const handleArchive = async () => {
    if (!customer) return;
    const confirmed = window.confirm(
      `Archive customer "${customer.full_name}"? The profile is kept and can be restored later.`
    );
    if (!confirmed) return;
    try {
      await archiveMutation.mutateAsync(customerId);
    } catch (archiveError) {
      window.alert(getApiErrorMessage(archiveError));
    }
  };

  const handleRestore = async () => {
    try {
      await restoreMutation.mutateAsync(customerId);
    } catch (restoreError) {
      window.alert(getApiErrorMessage(restoreError));
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !customer) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, py: 8 }}>
        <Alert severity="error">{getApiErrorMessage(error)}</Alert>
        <Button variant="outlined" onClick={() => refetch()}>
          Retry
        </Button>
        <Button color="inherit" onClick={() => navigate('/customers')}>
          Back to Customers
        </Button>
      </Box>
    );
  }

  const renderMeasurementFields = (m: Measurement) => {
    const fields = MEASUREMENT_FIELDS_BY_GARMENT[garmentTab];
    return (
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: 'repeat(2, 1fr)',
            sm: 'repeat(3, 1fr)',
            md: 'repeat(4, 1fr)',
          },
          gap: 2.5,
        }}
      >
        {fields.map((field: MeasurementFieldName) => (
          <Box key={field}>
            <Typography variant="caption" sx={{ color: '#94A3B8', display: 'block', fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 600 }}>
              {MEASUREMENT_FIELD_LABELS[field]}
            </Typography>
            <Typography sx={{ fontWeight: 600, color: '#0F172A' }}>
              {m[field] == null ? '-' : `${m[field]} in`}
            </Typography>
          </Box>
        ))}
      </Box>
    );
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
        <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
          Saamu Tailors ERP
        </Link>
        <Link underline="hover" color="inherit" href="/customers" sx={{ fontSize: '0.85rem' }}>
          Customers
        </Link>
        <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
          {customer.full_name}
        </Typography>
      </Breadcrumbs>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 2 }}>
        <Stack direction="row" spacing={1.5} alignItems="flex-start">
          <Tooltip title="Back to customers">
            <IconButton
              onClick={() => navigate('/customers')}
              sx={{ border: '1px solid #E2E8F0', borderRadius: '10px', color: '#475569' }}
            >
              <ArrowBackIcon />
            </IconButton>
          </Tooltip>
          <Box>
            <Stack direction="row" spacing={1} alignItems="center">
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {customer.full_name}
              </Typography>
              <Chip
                label={customer.is_active ? 'Active' : 'Archived'}
                size="small"
                sx={{
                  fontWeight: 600,
                  backgroundColor: customer.is_active ? '#DCFCE7' : '#F1F5F9',
                  color: customer.is_active ? '#15803D' : '#64748B',
                }}
              />
            </Stack>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              Customer #{customer.id} · {customer.mobile_number}
            </Typography>
          </Box>
        </Stack>

        {isStaff && (
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={() => setEditDialogOpen(true)}
            >
              Edit
            </Button>
            {customer.is_active ? (
              <Button variant="outlined" color="error" startIcon={<ArchiveIcon />} onClick={handleArchive}>
                Archive
              </Button>
            ) : (
              <Button
                variant="outlined"
                sx={{ color: '#15803D', borderColor: '#86EFAC' }}
                startIcon={<UnarchiveIcon />}
                onClick={handleRestore}
              >
                Restore
              </Button>
            )}
          </Stack>
        )}
      </Box>

      <Paper sx={{ p: 3, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 2.5 }}>
          Profile Details
        </Typography>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
            gap: 3,
          }}
        >
          <InfoCell icon={<PhoneIcon sx={{ fontSize: 18 }} />} label="Primary Mobile" value={customer.mobile_number} />
          <InfoCell
            icon={<PhoneIcon sx={{ fontSize: 18 }} />}
            label="Alternate Mobile"
            value={customer.alternate_mobile_number || '-'}
          />
          <InfoCell icon={<LocationOnIcon sx={{ fontSize: 18 }} />} label="Address" value={customer.address || '-'} />
          <InfoCell icon={<NotesIcon sx={{ fontSize: 18 }} />} label="Notes" value={customer.notes || '-'} />
          <InfoCell icon={<CalendarTodayIcon sx={{ fontSize: 18 }} />} label="Created" value={formatDate(customer.created_at)} />
          <InfoCell icon={<CalendarTodayIcon sx={{ fontSize: 18 }} />} label="Last Updated" value={formatDate(customer.updated_at)} />
        </Box>
      </Paper>

      <Paper sx={{ borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        <Box sx={{ px: 3, py: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
              <StraightenIcon fontSize="small" />
            </Box>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                Measurement Chart
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B' }}>
                All measurements are recorded in inches
              </Typography>
            </Box>
          </Stack>
        </Box>

        <Tabs
          value={garmentTab}
          onChange={(_event, value: GarmentType) => setGarmentTab(value)}
          sx={{
            px: 2,
            '& .MuiTab-root': { textTransform: 'none', fontWeight: 600 },
          }}
        >
          <Tab label="Shirt" value="SHIRT" />
          <Tab label="Pant" value="PANT" />
        </Tabs>
        <Divider />

        <Box sx={{ p: 3 }}>
          {measurementsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
              <CircularProgress size={28} />
            </Box>
          ) : measurementsError ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, py: 4 }}>
              <Alert severity="error">{getApiErrorMessage(measurementsError)}</Alert>
              <Button variant="outlined" onClick={() => refetchMeasurements()}>
                Retry
              </Button>
            </Box>
          ) : currentMeasurement ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Stack direction="row" spacing={1}>
                  <Chip
                    label={`Version ${currentMeasurement.version}`}
                    size="small"
                    variant="outlined"
                    sx={{ fontWeight: 600 }}
                  />
                  <Chip
                    label="Current"
                    size="small"
                    sx={{ fontWeight: 600, backgroundColor: '#DCFCE7', color: '#15803D' }}
                  />
                </Stack>
                {isStaff && (
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<EditIcon />}
                    onClick={() => openMeasurementDialog(garmentTab, currentMeasurement)}
                  >
                    New Version
                  </Button>
                )}
              </Stack>
              {renderMeasurementFields(currentMeasurement)}
            </Box>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, py: 6 }}>
              <Typography sx={{ color: '#64748B' }}>
                No {garmentTab} measurements recorded yet.
              </Typography>
              {isStaff && (
                <Button
                  variant="contained"
                  startIcon={<StraightenIcon />}
                  onClick={() => openMeasurementDialog(garmentTab, null)}
                  sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
                >
                  Add {garmentTab} Measurements
                </Button>
              )}
            </Box>
          )}

          {historyMeasurements.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5 }}>
                Version History
              </Typography>
              <Stack spacing={1.5}>
                {historyMeasurements.map((m) => (
                  <Paper key={m.id} variant="outlined" sx={{ p: 2, borderRadius: '10px' }}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5 }}>
                      <Chip label={`Version ${m.version}`} size="small" variant="outlined" sx={{ fontWeight: 600 }} />
                      <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                        Recorded {formatDate(m.updated_at)}
                      </Typography>
                    </Stack>
                    {renderMeasurementFields(m)}
                    {isStaff && (
                      <Box sx={{ mt: 1.5 }}>
                        <Button
                          size="small"
                          variant="outlined"
                          startIcon={<EditIcon />}
                          onClick={() => openMeasurementDialog(garmentTab, m)}
                        >
                          Update from this version
                        </Button>
                      </Box>
                    )}
                  </Paper>
                ))}
              </Stack>
            </Box>
          )}
        </Box>
      </Paper>

      <CustomerFormDialog
        open={editDialogOpen}
        initial={customer}
        onClose={() => setEditDialogOpen(false)}
        submit={(payload) => updateMutation.mutateAsync(payload)}
      />

      <MeasurementFormDialog
        open={measurementDialog.open}
        garmentType={measurementDialog.garment}
        lockGarment={measurementDialog.base !== null}
        initial={measurementDialog.base}
        onClose={closeMeasurementDialog}
        submit={handleMeasurementSubmit}
      />
    </Box>
  );
};
