import React from 'react';
import { Chip } from '@mui/material';
import {
  WORK_ASSIGNMENT_STATUS_COLORS,
  WORK_ASSIGNMENT_STATUS_LABELS,
} from '../types/tailors';
import type { WorkAssignmentStatus } from '../types/tailors';

const WorkAssignmentStatusChip: React.FC<{ status: WorkAssignmentStatus }> = ({ status }) => {
  const colors = WORK_ASSIGNMENT_STATUS_COLORS[status];
  return (
    <Chip
      label={WORK_ASSIGNMENT_STATUS_LABELS[status]}
      size="small"
      sx={{ fontWeight: 600, backgroundColor: colors.bg, color: colors.text }}
    />
  );
};

export default WorkAssignmentStatusChip;
