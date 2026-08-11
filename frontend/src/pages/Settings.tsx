import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';
import StorefrontIcon from '@mui/icons-material/Storefront';
import PersonIcon from '@mui/icons-material/Person';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '../context/useAuth';
import { useShopDetails, useUpdateShopDetails } from '../hooks/useSettings';
import { getApiErrorMessage } from '../utils/apiErrors';
import type { ShopDetailsPayload } from '../types/settings';
import { PageHeader } from '../components/ui/PageHeader';
import { SectionCard } from '../components/ui/SectionCard';
import { ErrorState } from '../components/ui/ErrorState';

const shopDetailsSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, 'Shop name is required')
    .max(100, 'Shop name must be 100 characters or fewer'),
  tagline: z.string().max(200, 'Tagline must be 200 characters or fewer'),
  address: z.string().max(2000, 'Address must be 2000 characters or fewer'),
  phone: z.string().max(30, 'Phone must be 30 characters or fewer'),
  established_year: z.coerce
    .number({ required_error: 'Enter the year the shop was established' })
    .int('Enter a valid year')
    .min(1000, 'Enter a valid year')
    .max(2100, 'Enter a valid year'),
});

type ShopDetailsFormData = z.infer<typeof shopDetailsSchema>;

export const Settings: React.FC = () => {
  const { user, role } = useAuth();
  const isStaff = role === 'STAFF';

  const { data, isLoading, isError, error, refetch } = useShopDetails();
  const updateMutation = useUpdateShopDetails();

  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const defaultValues = useMemo<ShopDetailsPayload>(
    () => ({ name: '', tagline: '', address: '', phone: '', established_year: 1954 }),
    []
  );

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors, isDirty, isSubmitting },
  } = useForm<ShopDetailsFormData>({
    resolver: zodResolver(shopDetailsSchema),
    defaultValues,
  });

  useEffect(() => {
    if (data) {
      reset({
        name: data.name,
        tagline: data.tagline,
        address: data.address,
        phone: data.phone,
        established_year: data.established_year,
      });
    }
  }, [data, reset]);

  useEffect(() => {
    if (isDirty) {
      setSuccessMessage(null);
    }
  }, [isDirty]);

  const onSubmit = async (values: ShopDetailsFormData) => {
    setSubmitError(null);
    setSuccessMessage(null);
    try {
      const saved = await updateMutation.mutateAsync(values);
      reset({
        name: saved.name,
        tagline: saved.tagline,
        address: saved.address,
        phone: saved.phone,
        established_year: saved.established_year,
      });
      setSuccessMessage('Shop details saved.');
    } catch (submitErr) {
      setSubmitError(getApiErrorMessage(submitErr));
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <PageHeader
        title="Settings"
        subtitle="Manage the business profile and review the current account."
        icon={<SettingsIcon />}
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Settings' }]}
      />

      <Stack spacing={3}>
        <SectionCard title="Current Account" icon={<PersonIcon />}>
          <Stack spacing={1}>
            <AccountRow label="Username" value={user?.username ?? '—'} />
            <AccountRow
              label="Role"
              value={role === 'OWNER' ? 'Owner' : role === 'STAFF' ? 'Staff' : '—'}
            />
            <AccountRow label="Status" value={user?.is_active ? 'Active' : 'Inactive'} />
          </Stack>
        </SectionCard>

        <SectionCard title="Shop Details" icon={<StorefrontIcon />}>
          <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
            This profile appears on the digital bill and customer communications.
          </Typography>

          {!isStaff && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Owners have view-only access to settings. Staff users manage the shop profile.
            </Alert>
          )}

          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
              <CircularProgress size={28} />
            </Box>
          ) : isError ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <ErrorState message={getApiErrorMessage(error)} onRetry={() => refetch()} />
            </Box>
          ) : (
            <>
              {successMessage && <Alert severity="success">{successMessage}</Alert>}
              {submitError && <Alert severity="error">{submitError}</Alert>}

              <Stack spacing={2.5} sx={{ mt: 2 }}>
                <Stack spacing={2.5} direction={{ xs: 'column', sm: 'row' }}>
                  <Controller
                    name="name"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Shop Name *"
                        fullWidth
                        size="small"
                        disabled={!isStaff}
                        error={!!errors.name}
                        helperText={errors.name?.message}
                      />
                    )}
                  />
                  <Controller
                    name="established_year"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Established Year *"
                        type="number"
                        inputProps={{ min: 1000, max: 2100, step: 1 }}
                        fullWidth
                        size="small"
                        disabled={!isStaff}
                        error={!!errors.established_year}
                        helperText={errors.established_year?.message}
                      />
                    )}
                  />
                </Stack>
                <Controller
                  name="tagline"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Tagline"
                      fullWidth
                      size="small"
                      disabled={!isStaff}
                      error={!!errors.tagline}
                      helperText={errors.tagline?.message}
                    />
                  )}
                />
                <Controller
                  name="phone"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Phone"
                      fullWidth
                      size="small"
                      disabled={!isStaff}
                      error={!!errors.phone}
                      helperText={errors.phone?.message}
                    />
                  )}
                />
                <Controller
                  name="address"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Address"
                      fullWidth
                      size="small"
                      multiline
                      minRows={2}
                      disabled={!isStaff}
                      error={!!errors.address}
                      helperText={errors.address?.message}
                    />
                  )}
                />

                {isStaff && (
                  <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                      type="submit"
                      variant="contained"
                      disabled={isSubmitting || !isDirty}
                      startIcon={isSubmitting ? <CircularProgress size={16} color="inherit" /> : undefined}
                      onClick={handleSubmit(onSubmit)}
                    >
                      {isSubmitting ? 'Saving…' : 'Save Changes'}
                    </Button>
                  </Box>
                )}
              </Stack>
            </>
          )}
        </SectionCard>
      </Stack>
    </Box>
  );
};

const AccountRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
    <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 500 }}>
      {label}
    </Typography>
    <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary' }}>
      {value}
    </Typography>
  </Box>
);

export default Settings;
