import React, { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import RefreshIcon from '@mui/icons-material/Refresh';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';
import ChatIcon from '@mui/icons-material/Chat';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { useNavigate } from 'react-router-dom';
import { useReminderList } from '../hooks/useReminders';
import { useReminderActions } from '../hooks/useReminderActions';
import { getApiErrorMessage } from '../utils/apiErrors';
import { PageHeader } from '../components/ui/PageHeader';
import { AppPagination } from '../components/ui/AppPagination';
import { StatusBadge } from '../components/ui/StatusBadge';
import type { StatusTone } from '../components/ui/StatusBadge';
import { ORDER_STATUS_LABELS } from '../types/orders';
import type { OrderStatus } from '../types/orders';
import type { ReminderCandidate } from '../types/reminders';
const PAGE_SIZE = 6;

const ORDER_STATUS_TONES: Record<OrderStatus, StatusTone> = {
  NEW: 'gold',
  CUTTING: 'warning',
  STITCHING: 'info',
  READY: 'success',
  COLLECTED: 'neutral',
  CANCELLED: 'error',
};

const ReminderCard: React.FC<{ reminder: ReminderCandidate }> = ({ reminder }) => {
  const navigate = useNavigate();
  const { copied, isOpening, error, copy, open } = useReminderActions(reminder);
  const usableNumber = reminder.whatsapp_url !== null;

  return (
    <Paper sx={{ p: 3, borderRadius: '12px', border: '1px solid #E7E0D0' }}>
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        spacing={2}
        alignItems={{ xs: 'flex-start', sm: 'center' }}
        justifyContent="space-between"
      >
        <Stack direction="row" spacing={1.5} alignItems="center">
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: '10px',
              backgroundColor: '#F5EBD2',
              color: '#A98216',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <NotificationsActiveIcon fontSize="small" />
          </Box>
          <Box>
            <Stack direction="row" spacing={1} alignItems="center">
              <Typography sx={{ fontWeight: 700 }}>{reminder.reminder_type_label}</Typography>
              <StatusBadge
                label={ORDER_STATUS_LABELS[reminder.order.status]}
                tone={ORDER_STATUS_TONES[reminder.order.status]}
              />
            </Stack>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              {reminder.order.order_number} · {reminder.customer.full_name}
            </Typography>
          </Box>
        </Stack>
        <Button
          size="small"
          variant="outlined"
          startIcon={<VisibilityIcon fontSize="small" />}
          onClick={() => navigate(`/orders/${reminder.order.id}`)}
        >
          View Order
        </Button>
      </Stack>

      <Paper
        variant="outlined"
        sx={{
          mt: 2,
          p: 2,
          borderRadius: '10px',
          backgroundColor: '#FBF6EA',
          maxHeight: 240,
          overflow: 'auto',
        }}
      >
        <Typography
          component="pre"
          sx={{
            m: 0,
            whiteSpace: 'pre-wrap',
            fontFamily: 'inherit',
            fontSize: '0.875rem',
            color: 'text.primary',
          }}
        >
          {reminder.message}
        </Typography>
      </Paper>

      {!usableNumber && (
        <Typography variant="body2" sx={{ color: 'warning.dark', mt: 1.5 }}>
          No usable WhatsApp number is recorded for this customer, so Open
          WhatsApp is disabled. The message can still be copied.
        </Typography>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 1.5 }}>
          {error}
        </Alert>
      )}

      <Stack direction="row" spacing={1.5} sx={{ mt: 2 }} flexWrap="wrap">
        <Button
          variant="outlined"
          startIcon={copied ? <CheckIcon /> : <ContentCopyIcon />}
          disabled={isOpening}
          onClick={copy}
          sx={copied ? { color: 'success.dark', borderColor: 'success.light' } : undefined}
        >
          {copied ? 'Copied' : 'Copy WhatsApp Message'}
        </Button>
        <Button
          variant="contained"
          startIcon={<ChatIcon />}
          disabled={!usableNumber || isOpening}
          onClick={open}
        >
          {isOpening ? 'Preparing...' : 'Open WhatsApp'}
        </Button>
      </Stack>
    </Paper>
  );
};

export const Reminders: React.FC = () => {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, isFetching, refetch } = useReminderList(page);

  const reminders = data?.results ?? [];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <PageHeader
        title="Reminders"
        subtitle="Review and prepare customer reminders. Nothing is sent automatically."
        icon={<NotificationsActiveIcon />}
        crumbs={[{ label: 'Dashboard', to: '/dashboard' }, { label: 'Reminders' }]}
        actions={
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
            disabled={isFetching}
          >
            Refresh
          </Button>
        }
      />

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
          <CircularProgress />
        </Box>
      )}

      {isError && !isLoading && (
        <Paper sx={{ p: 3, borderRadius: '12px', border: '1px solid #FBE9E6', backgroundColor: '#FEF2F2' }}>
          <Stack direction="row" spacing={1.5} alignItems="center" justifyContent="space-between">
            <Alert severity="error" sx={{ flex: 1 }}>
              {getApiErrorMessage(error)}
            </Alert>
            <Button variant="outlined" size="small" onClick={() => refetch()}>
              Retry
            </Button>
          </Stack>
        </Paper>
      )}

      {!isLoading && !isError && reminders.length === 0 && (
        <Paper sx={{ p: 6, borderRadius: '12px', border: '1px solid #E7E0D0', textAlign: 'center' }}>
          <Typography variant="body1" sx={{ color: 'text.secondary' }}>
            No pending reminders. Reminders appear here for active orders that
            are ready for collection or have an outstanding balance.
          </Typography>
        </Paper>
      )}

      {!isLoading && !isError && reminders.length > 0 && (
        <>
          <Stack spacing={2}>
            {reminders.map((reminder) => (
              <ReminderCard key={reminder.id} reminder={reminder} />
            ))}
          </Stack>

          {data && data.count > 0 && (
            <AppPagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />
          )}
        </>
      )}
    </Box>
  );
};
