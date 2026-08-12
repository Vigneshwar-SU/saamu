import React from 'react';
import { Box, Button, Divider, Popover, Skeleton, Stack, Typography } from '@mui/material';
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNone';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import RefreshIcon from '@mui/icons-material/Refresh';
import { NotificationItem } from './NotificationItem';
import type { NotificationGroup } from '../../hooks/useNotifications';

interface NotificationPopoverProps {
  open: boolean;
  anchorEl: HTMLElement | null;
  onClose: () => void;
  onViewAll: () => void;
  onSelectGroup: (group: NotificationGroup) => void;
  groups: NotificationGroup[];
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
}

export const NotificationPopover: React.FC<NotificationPopoverProps> = ({
  open,
  anchorEl,
  onClose,
  onViewAll,
  onSelectGroup,
  groups,
  isLoading,
  isError,
  onRetry,
}) => {
  return (
    <Popover
      open={open}
      anchorEl={anchorEl}
      onClose={onClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      marginThreshold={8}
      PaperProps={{
        elevation: 3,
        sx: {
          width: { xs: 'calc(100vw - 24px)', sm: 380, md: 400 },
          mt: 1,
          borderRadius: '14px',
          border: '1px solid #E7E0D0',
          boxShadow: '0 18px 40px -12px rgba(58, 48, 20, 0.25)',
          overflow: 'hidden',
        },
      }}
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', maxHeight: 'min(70vh, 520px)' }}>
        {/* Header */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            px: 2,
            py: 1.5,
            borderBottom: '1px solid #E7E0D0',
          }}
        >
          <Typography sx={{ fontWeight: 700, fontSize: '0.9375rem' }}>Notifications</Typography>
          <Button size="small" sx={{ fontSize: '0.8125rem', fontWeight: 600 }} onClick={onViewAll}>
            View All
          </Button>
        </Box>

        {/* Body */}
        <Box sx={{ overflowY: 'auto', px: 1, py: 0.5 }}>
          {isLoading && (
            <Stack spacing={0.5} sx={{ py: 0.5 }}>
              {[0, 1, 2, 3].map((index) => (
                <Box
                  key={index}
                  sx={{ display: 'flex', alignItems: 'center', gap: 1.5, px: 1, py: 1 }}
                >
                  <Skeleton variant="circular" width={10} height={10} />
                  <Box sx={{ flex: 1 }}>
                    <Skeleton width="70%" height={16} />
                    <Skeleton width="45%" height={12} />
                  </Box>
                </Box>
              ))}
            </Stack>
          )}

          {!isLoading && isError && (
            <Box sx={{ px: 2, py: 4, textAlign: 'center' }}>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                Couldn't load notifications.
              </Typography>
              <Button
                size="small"
                variant="outlined"
                startIcon={<RefreshIcon fontSize="small" />}
                onClick={onRetry}
                sx={{ mt: 1.5 }}
              >
                Retry
              </Button>
            </Box>
          )}

          {!isLoading && !isError && groups.length === 0 && (
            <Box sx={{ px: 2, py: 5, textAlign: 'center' }}>
              <Box
                sx={{
                  width: 48,
                  height: 48,
                  mx: 'auto',
                  borderRadius: '14px',
                  backgroundColor: '#F5EBD2',
                  color: '#A98216',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mb: 1.5,
                }}
              >
                <NotificationsNoneIcon />
              </Box>
              <Typography sx={{ fontWeight: 600, fontSize: '0.9375rem' }}>
                You're all caught up
              </Typography>
              <Typography
                variant="body2"
                sx={{ color: 'text.secondary', mt: 0.5, maxWidth: 260, mx: 'auto' }}
              >
                No urgent orders, payments, or reminders need attention right now.
              </Typography>
            </Box>
          )}

          {!isLoading && !isError && groups.length > 0 && (
            <Stack divider={<Divider sx={{ mx: 1.5 }} />} spacing={0}>
              {groups.map((group) => (
                <NotificationItem
                  key={group.reminderType}
                  group={group}
                  onClick={() => onSelectGroup(group)}
                />
              ))}
            </Stack>
          )}
        </Box>

        {/* Footer */}
        <Box sx={{ borderTop: '1px solid #E7E0D0' }}>
          <Button
            fullWidth
            onClick={onViewAll}
            endIcon={<ArrowForwardIcon fontSize="small" />}
            sx={{
              justifyContent: 'space-between',
              px: 2.5,
              py: 1.25,
              color: '#7A5E0C',
              fontWeight: 600,
              fontSize: '0.875rem',
              borderRadius: 0,
              '&:hover': {
                backgroundColor: '#FBF6EA',
              },
            }}
          >
            View All Reminders
          </Button>
        </Box>
      </Box>
    </Popover>
  );
};

export default NotificationPopover;
