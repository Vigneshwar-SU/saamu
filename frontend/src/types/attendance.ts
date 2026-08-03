import type { Tailor } from './tailors';

export const ATTENDANCE_STATUSES = ['PRESENT', 'ABSENT', 'HALF_DAY'] as const;

export type AttendanceStatus = (typeof ATTENDANCE_STATUSES)[number];

export const ATTENDANCE_STATUS_LABELS: Record<AttendanceStatus, string> = {
  PRESENT: 'Present',
  ABSENT: 'Absent',
  HALF_DAY: 'Half Day',
};

export const ATTENDANCE_STATUS_COLORS: Record<AttendanceStatus, { bg: string; text: string }> = {
  PRESENT: { bg: '#DCFCE7', text: '#15803D' },
  ABSENT: { bg: '#FEE2E2', text: '#B91C1C' },
  HALF_DAY: { bg: '#FEF3C7', text: '#B45309' },
};

export interface Attendance {
  id: number;
  tailor: Tailor;
  attendance_date: string;
  status: AttendanceStatus;
  notes: string;
  marked_by: number | null;
  marked_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface AttendanceListResult {
  count: number;
  next: string | null;
  previous: string | null;
  results: Attendance[];
}

export interface AttendanceListParams {
  tailor?: number;
  date_from?: string;
  date_to?: string;
  status?: AttendanceStatus | '';
  page?: number;
}

export interface AttendancePayload {
  tailor: number;
  attendance_date: string;
  status: AttendanceStatus;
  notes?: string;
}
