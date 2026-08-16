import React, { useState } from 'react';
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Stack,
  Tab,
  Tabs,
  Typography,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import ArchiveIcon from '@mui/icons-material/Archive';
import UnarchiveIcon from '@mui/icons-material/Unarchive';
import PhoneIcon from '@mui/icons-material/Phone';
import StraightenIcon from '@mui/icons-material/Straighten';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { formatDate } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiErrors';
import { normalizeFullName, normalizeMobileNumber } from '../utils/normalization';
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
import { MEASUREMENT_FIELD_LABELS, MEASUREMENT_FIELDS_BY_GARMENT } from '../types/customers';
import type {
  GarmentType,
  Measurement,
  MeasurementFieldName,
  MeasurementPayload,
} from '../types/customers';
import { PageHeader } from '../components/ui/PageHeader';
import { SectionCard } from '../components/ui/SectionCard';
import { InfoField } from '../components/ui/InfoField';
import { StatusBadge } from '../components/ui/StatusBadge';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { ErrorState } from '../components/ui/ErrorState';
import { EmptyState } from '../components/ui/EmptyState';

interface MeasurementDialogState {
  open: boolean;
  garment: GarmentType;
  base: Measurement | null;
}

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
  const [archiveDialogOpen, setArchiveDialogOpen] = useState(false);
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
    setArchiveDialogOpen(false);
    if (!customer) return;
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
        <ErrorState message={getApiErrorMessage(error)} onRetry={() => refetch()} />
        <Button color="inherit" onClick={() => navigate('/customers')}>
          Back to Customers
        </Button>
      </Box>
    );
  }

  const displayName = normalizeFullName(customer.full_name);
  const displayPrimaryMobile = normalizeMobileNumber(customer.mobile_number);
  const displayAlternateMobile = customer.alternate_mobile_number
    ? normalizeMobileNumber(customer.alternate_mobile_number)
    : '-';

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
            <Typography
              variant="caption"
              sx={{
                color: 'text.disabled',
                display: 'block',
                fontSize: '0.7rem',
                textTransform: 'uppercase',
                fontWeight: 600,
              }}
            >
              {MEASUREMENT_FIELD_LABELS[field]}
            </Typography>
            <Typography sx={{ fontWeight: 600, color: 'text.primary' }}>
              {m[field] == null ? '-' : `${m[field]} in`}
            </Typography>
          </Box>
        ))}
      </Box>
    );
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <PageHeader
        title={displayName}
        subtitle={`Customer #${customer.id} · ${displayPrimaryMobile}`}
        icon={<StraightenIcon />}
        backTo="/customers"
        crumbs={[
          { label: 'Dashboard', to: '/dashboard' },
          { label: 'Customers', to: '/customers' },
          { label: displayName },
        ]}
        actions={
          isStaff && (
            <Stack direction="row" spacing={1} flexWrap="wrap">
              <Button
                variant="outlined"
                startIcon={<EditIcon />}
                onClick={() => setEditDialogOpen(true)}
              >
                Edit
              </Button>
              {customer.is_active ? (
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<ArchiveIcon />}
                  onClick={() => setArchiveDialogOpen(true)}
                >
                  Archive
                </Button>
              ) : (
                <Button
                  variant="outlined"
                  sx={{ color: '#1F5C3C', borderColor: '#86EFAC' }}
                  startIcon={<UnarchiveIcon />}
                  onClick={handleRestore}
                >
                  Restore
                </Button>
              )}
            </Stack>
          )
        }
      />

      <SectionCard title="Profile Details" icon={<PhoneIcon />}>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
            gap: 3,
          }}
        >
          <InfoField
            label="Status"
            value={
              <StatusBadge
                label={customer.is_active ? 'Active' : 'Archived'}
                tone={customer.is_active ? 'success' : 'neutral'}
              />
            }
            strong
          />
          <InfoField label="Primary Mobile" value={displayPrimaryMobile} />
          <InfoField label="Alternate Mobile" value={displayAlternateMobile} />
          <InfoField label="Address" value={customer.address || '-'} />
          <InfoField label="Notes" value={customer.notes || '-'} />
          <InfoField label="Created" value={formatDate(customer.created_at)} />
          <InfoField label="Last Updated" value={formatDate(customer.updated_at)} />
        </Box>
      </SectionCard>

      <SectionCard
        title="Measurement Chart"
        subtitle="All measurements are recorded in inches"
        icon={<StraightenIcon />}
        noPadding
      >
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
            <Box
              sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, py: 4 }}
            >
              <ErrorState
                message={getApiErrorMessage(measurementsError)}
                onRetry={() => refetchMeasurements()}
              />
            </Box>
          ) : currentMeasurement ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                spacing={1}
                alignItems={{ xs: 'stretch', sm: 'center' }}
                justifyContent="space-between"
              >
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
                    sx={{ fontWeight: 600, backgroundColor: '#E7F1EA', color: '#1F5C3C' }}
                  />
                </Stack>
                {isStaff && (
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<EditIcon />}
                    onClick={() => openMeasurementDialog(garmentTab, currentMeasurement)}
                    sx={{ width: { xs: '100%', sm: 'auto' } }}
                  >
                    New Version
                  </Button>
                )}
              </Stack>
              {renderMeasurementFields(currentMeasurement)}
            </Box>
          ) : (
            <EmptyState
              title={`No ${garmentTab} measurements yet`}
              message={`Record the customer's ${garmentTab} measurements to get started.`}
              action={
                isStaff ? (
                  <Button
                    variant="contained"
                    startIcon={<StraightenIcon />}
                    onClick={() => openMeasurementDialog(garmentTab, null)}
                  >
                    Add {garmentTab} Measurements
                  </Button>
                ) : undefined
              }
            />
          )}

          {historyMeasurements.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5 }}>
                Version History
              </Typography>
              <Stack spacing={1.5}>
                {historyMeasurements.map((m) => (
                  <Box
                    key={m.id}
                    sx={{
                      p: 2,
                      borderRadius: '10px',
                      border: '1px solid #E7E0D0',
                      backgroundColor: '#FBF6EA',
                    }}
                  >
                    <Stack
                      direction={{ xs: 'column', sm: 'row' }}
                      spacing={1}
                      alignItems={{ xs: 'flex-start', sm: 'center' }}
                      justifyContent="space-between"
                      sx={{ mb: 1.5 }}
                    >
                      <Chip
                        label={`Version ${m.version}`}
                        size="small"
                        variant="outlined"
                        sx={{ fontWeight: 600 }}
                      />
                      <Typography variant="caption" sx={{ color: 'text.disabled' }}>
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
                  </Box>
                ))}
              </Stack>
            </Box>
          )}
        </Box>
      </SectionCard>

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

      <ConfirmDialog
        open={archiveDialogOpen}
        title="Archive Customer"
        message={`Archive customer "${displayName}"? The profile is kept and can be restored later.`}
        confirmLabel="Archive"
        tone="error"
        loading={archiveMutation.isPending}
        onConfirm={handleArchive}
        onCancel={() => setArchiveDialogOpen(false)}
      />
    </Box>
  );
};

export default CustomerDetail;
