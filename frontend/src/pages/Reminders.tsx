import React, { useState } from 'react';
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  CircularProgress,
  Link,
  Pagination,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
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
import { ORDER_STATUS_COLORS, ORDER_STATUS_LABELS } from '../types/orders';
import type { ReminderCandidate } from '../types/reminders';
const PAGE_SIZE = 20;

const ReminderCard: React.FC<{ reminder: ReminderCandidate }> = ({ reminder }) => {
  const navigate = useNavigate();
  const { copied, isOpening, error, copy, open } = useReminderActions(reminder);
  const colors = ORDER_STATUS_COLORS[reminder.order.status];
  const usableNumber = reminder.whatsapp_url !== null;

  return (
    <Paper sx={{ p: 3, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
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
              backgroundColor: '#EFF6FF',
              color: '#1E3A8A',
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
              <Chip
                size="small"
                label={ORDER_STATUS_LABELS[reminder.order.status]}
                sx={{ fontWeight: 600, backgroundColor: colors.bg, color: colors.text }}
              />
            </Stack>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
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
          backgroundColor: '#F8FAFC',
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
            color: '#0F172A',
          }}
        >
          {reminder.message}
        </Typography>
      </Paper>

      {!usableNumber && (
        <Typography variant="body2" sx={{ color: '#B45309', mt: 1.5 }}>
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
          sx={copied ? { color: '#15803D', borderColor: '#86EFAC' } : undefined}
        >
          {copied ? 'Copied' : 'Copy WhatsApp Message'}
        </Button>
        <Button
          variant="contained"
          startIcon={<ChatIcon />}
          disabled={!usableNumber || isOpening}
          onClick={open}
          sx={{ backgroundColor: '#1E3A8A', '&:hover': { backgroundColor: '#1D4ED8' } }}
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

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;
  const reminders = data?.results ?? [];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
        <Link underline="hover" color="inherit" href="/dashboard" sx={{ fontSize: '0.85rem' }}>
          Saamu Tailors ERP
        </Link>
        <Typography color="text.primary" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
          Reminders
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
            <NotificationsActiveIcon />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              Reminders
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              Review and prepare customer reminders. Nothing is sent automatically.
            </Typography>
          </Box>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => refetch()}
          disabled={isFetching}
        >
          Refresh
        </Button>
      </Box>

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
          <CircularProgress />
        </Box>
      )}

      {isError && !isLoading && (
        <Paper sx={{ p: 3, borderRadius: '12px', border: '1px solid #FECACA', backgroundColor: '#FEF2F2' }}>
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
        <Paper sx={{ p: 6, borderRadius: '12px', border: '1px solid #E2E8F0', textAlign: 'center' }}>
          <Typography variant="body1" sx={{ color: '#64748B' }}>
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
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="body2" sx={{ color: '#64748B' }}>
                Showing {reminders.length} of {data.count} reminders
              </Typography>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(_event, value) => setPage(value)}
                color="primary"
              />
            </Box>
          )}
        </>
      )}
    </Box>
  );
};
