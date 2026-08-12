import React from 'react';
import { Box, ButtonBase, Typography } from '@mui/material';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import type { NotificationGroup } from '../../hooks/useNotifications';

const TONE_DOT: Record<NotificationGroup['tone'], string> = {
  error: '#B3402F',
  warning: '#C97A2E',
  success: '#2E7D52',
  info: '#3F6D9C',
  gold: '#C9A227',
  neutral: '#A29B8E',
};

interface NotificationItemProps {
  group: NotificationGroup;
  onClick: () => void;
}

/**
 * One aggregated notification row: severity dot, count + category title and a
 * short context line. Clicking navigates to the relevant record/page.
 */
export const NotificationItem: React.FC<NotificationItemProps> = ({ group, onClick }) => {
  return (
    <ButtonBase
      onClick={onClick}
      aria-label={`${group.count} ${group.label}`}
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1.5,
        width: '100%',
        minHeight: 56,
        px: 2,
        py: 1,
        borderRadius: '10px',
        textAlign: 'left',
        justifyContent: 'flex-start',
        '&:hover': {
          backgroundColor: '#FBF6EA',
        },
        '&:active': {
          backgroundColor: '#F5EBD2',
        },
      }}
    >
      <Box
        sx={{
          width: 10,
          height: 10,
          borderRadius: '50%',
          backgroundColor: TONE_DOT[group.tone],
          flexShrink: 0,
        }}
      />
      <Box sx={{ minWidth: 0, flex: 1 }}>
        <Typography
          sx={{
            fontWeight: 600,
            fontSize: '0.875rem',
            lineHeight: 1.3,
            color: 'text.primary',
          }}
          noWrap
        >
          {group.count} {group.label}
        </Typography>
        <Typography
          variant="caption"
          sx={{ color: 'text.secondary', display: 'block', lineHeight: 1.4 }}
          noWrap
        >
          {group.subtitle}
        </Typography>
      </Box>
      <ChevronRightIcon sx={{ color: 'text.disabled', fontSize: 18, flexShrink: 0 }} />
    </ButtonBase>
  );
};

export default NotificationItem;
