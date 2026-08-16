import React, { useEffect, useMemo, useState } from 'react';
import { Alert, Box, Button, CircularProgress, Stack, TextField, Typography } from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';
import StorefrontIcon from '@mui/icons-material/Storefront';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import ForumIcon from '@mui/icons-material/Forum';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '../context/useAuth';
import { useHealth } from '../hooks/useHealth';
import { useShopDetails, useUpdateShopDetails } from '../hooks/useSettings';
import { getApiErrorMessage } from '../utils/apiErrors';
import type { ShopDetailsPayload } from '../types/settings';
import { ORDER_MESSAGE_TYPE_LABELS } from '../types/communications';
import { PageHeader } from '../components/ui/PageHeader';
import { SectionCard } from '../components/ui/SectionCard';
import { ErrorState } from '../components/ui/ErrorState';
import { InfoField } from '../components/ui/InfoField';
import { StatusBadge } from '../components/ui/StatusBadge';

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
  customer_follow_up_months: z.coerce
    .number({ required_error: 'Enter the follow-up period in months' })
    .int('Enter a whole number of months')
    .min(1, 'Follow-up period must be at least 1 month')
    .max(60, 'Follow-up period must be 60 months or fewer'),
});

type ShopDetailsFormData = z.infer<typeof shopDetailsSchema>;

const COMMUNICATION_MESSAGES: { label: string; description: string }[] = [
  {
    label: ORDER_MESSAGE_TYPE_LABELS.ORDER_RECEIVED,
    description:
      'Sent when a new order is placed. Includes the order number, items, totals, payment balance and expected delivery date.',
  },
  {
    label: ORDER_MESSAGE_TYPE_LABELS.ORDER_IN_PROGRESS,
    description:
      'Sent while an order is being tailored. Shares the current status and the next expected step.',
  },
  {
    label: ORDER_MESSAGE_TYPE_LABELS.READY_FOR_COLLECTION,
    description:
      'Sent when an order is ready. Includes the shop address and phone number for collection.',
  },
  {
    label: ORDER_MESSAGE_TYPE_LABELS.COLLECTED_SETTLED,
    description:
      'Sent after collection when the order is fully settled, confirming the payment status.',
  },
  {
    label: ORDER_MESSAGE_TYPE_LABELS.COLLECTED_PAYMENT_PENDING,
    description: 'Sent after collection when a balance remains outstanding, requesting payment.',
  },
];

export const Settings: React.FC = () => {
  const { user, role } = useAuth();
  const isStaff = role === 'STAFF';

  const { data, isLoading, isError, error, refetch } = useShopDetails();
  const updateMutation = useUpdateShopDetails();
  const { data: health, isSuccess: healthSuccess, isError: healthError } = useHealth();

  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const defaultValues = useMemo<ShopDetailsPayload>(
    () => ({
      name: '',
      tagline: '',
      address: '',
      phone: '',
      established_year: 1954,
      customer_follow_up_months: 6,
    }),
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
        customer_follow_up_months: data.customer_follow_up_months,
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
        customer_follow_up_months: saved.customer_follow_up_months,
      });
      setSuccessMessage('Settings saved.');
    } catch (submitErr) {
      setSubmitError(getApiErrorMessage(submitErr));
    }
  };

  const backendOnline = healthSuccess;
  const databaseOk = health?.database === 'ok';

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <PageHeader
        title="Settings"
        subtitle="Manage the shop profile, reminders and communication preferences."
        icon={<SettingsIcon />}
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Settings' }]}
      />

      {isLoading ? (
        <SectionCard title="Loading" icon={<SettingsIcon />}>
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
            <CircularProgress size={28} />
          </Box>
        </SectionCard>
      ) : isError ? (
        <SectionCard title="Settings" icon={<SettingsIcon />}>
          <ErrorState message={getApiErrorMessage(error)} onRetry={() => refetch()} />
        </SectionCard>
      ) : (
        <Stack spacing={3}>
          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <Stack spacing={3}>
              <SectionCard
                title="Shop Information"
                subtitle="This profile appears on the digital bill and in customer communications."
                icon={<StorefrontIcon />}
              >
                {!isStaff && (
                  <Alert severity="info" sx={{ mb: 2.5 }}>
                    Owners have view-only access to settings. Staff users manage the shop profile.
                  </Alert>
                )}

                <Stack spacing={2.5}>
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
                </Stack>
              </SectionCard>

              <SectionCard
                title="Reminder Settings"
                subtitle="Control how long a customer can stay inactive before a follow-up reminder is generated."
                icon={<NotificationsActiveIcon />}
              >
                <Controller
                  name="customer_follow_up_months"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Follow-up Period (months)"
                      type="number"
                      inputProps={{ min: 1, max: 60, step: 1 }}
                      fullWidth
                      size="small"
                      disabled={!isStaff}
                      error={!!errors.customer_follow_up_months}
                      helperText={
                        errors.customer_follow_up_months?.message ||
                        'Customers who have not placed an order within this period can appear in the Reminders section.'
                      }
                    />
                  )}
                />
              </SectionCard>

              {isStaff && (
                <Stack spacing={1.5}>
                  {successMessage && <Alert severity="success">{successMessage}</Alert>}
                  {submitError && <Alert severity="error">{submitError}</Alert>}
                  <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                      type="submit"
                      variant="contained"
                      disabled={isSubmitting || !isDirty}
                      startIcon={
                        isSubmitting ? <CircularProgress size={16} color="inherit" /> : undefined
                      }
                    >
                      {isSubmitting ? 'Saving…' : 'Save Changes'}
                    </Button>
                  </Box>
                </Stack>
              )}
            </Stack>
          </form>

          <SectionCard
            title="Communication"
            subtitle="Standardized messages are generated automatically from the order status and payment balance."
            icon={<ForumIcon />}
          >
            <Stack spacing={2}>
              {COMMUNICATION_MESSAGES.map((message) => (
                <Box key={message.label}>
                  <Typography sx={{ fontWeight: 600, fontSize: '0.9375rem' }}>
                    {message.label}
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    {message.description}
                  </Typography>
                </Box>
              ))}
              <Alert severity="info" sx={{ mt: 1 }}>
                Nothing is sent automatically — staff copy the message or open WhatsApp from the
                order page. Customer follow-up reminders are generated after the period set in
                Reminder Settings.
              </Alert>
            </Stack>
          </SectionCard>

          <SectionCard
            title="System Information"
            subtitle="Read-only details about the application and its current status."
            icon={<InfoOutlinedIcon />}
          >
            <Stack spacing={1}>
              <Stack
                spacing={2.5}
                direction={{ xs: 'column', sm: 'row' }}
                sx={{ flexWrap: 'wrap' }}
              >
                <Box sx={{ flex: '1 1 220px' }}>
                  <InfoField label="App" value="Saamu Tailors ERP" strong />
                </Box>
                <Box sx={{ flex: '1 1 220px' }}>
                  <InfoField label="Version" value={health?.version ? `v${health.version}` : '—'} />
                </Box>
                <Box sx={{ flex: '1 1 220px' }}>
                  <InfoField
                    label="Environment"
                    value={import.meta.env.DEV ? 'Local Server' : 'Production'}
                  />
                </Box>
              </Stack>
              <Stack
                spacing={2.5}
                direction={{ xs: 'column', sm: 'row' }}
                sx={{ flexWrap: 'wrap' }}
              >
                <Box sx={{ flex: '1 1 220px' }}>
                  <InfoField
                    label="Backend"
                    value={
                      <StatusBadge
                        label={healthError ? 'Offline' : backendOnline ? 'Online' : 'Checking…'}
                        tone={healthError ? 'error' : backendOnline ? 'success' : 'neutral'}
                      />
                    }
                  />
                </Box>
                <Box sx={{ flex: '1 1 220px' }}>
                  <InfoField
                    label="Database"
                    value={
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          PostgreSQL
                        </Typography>
                        <StatusBadge
                          label={databaseOk ? 'Operational' : 'Unavailable'}
                          tone={databaseOk ? 'success' : 'error'}
                        />
                      </Stack>
                    }
                  />
                </Box>
                <Box sx={{ flex: '1 1 220px' }}>
                  <InfoField
                    label="Signed in as"
                    value={`${user?.username ?? '—'} (${role === 'OWNER' ? 'Owner' : role === 'STAFF' ? 'Staff' : '—'})`}
                  />
                </Box>
              </Stack>
            </Stack>
          </SectionCard>
        </Stack>
      )}
    </Box>
  );
};

export default Settings;
