import React from 'react';
import { Badge } from '@mui/material';

interface NotificationBadgeProps {
  count: number;
  children: React.ReactNode;
}

/**
 * Gold count badge for the notification bell. Renders nothing extra when there
 * are no actionable reminders so the header never shows a misleading zero.
 */
export const NotificationBadge: React.FC<NotificationBadgeProps> = ({ count, children }) => {
  if (count <= 0) {
    return <>{children}</>;
  }

  return (
    <Badge
      overlap="circular"
      badgeContent={count > 99 ? '99+' : count}
      sx={{
        '& .MuiBadge-badge': {
          backgroundColor: '#C9A227',
          color: '#FFFFFF',
          fontWeight: 700,
          fontSize: '0.65rem',
          height: 18,
          minWidth: 18,
          borderRadius: 9,
          padding: '0 4px',
        },
      }}
    >
      {children}
    </Badge>
  );
};

export default NotificationBadge;
