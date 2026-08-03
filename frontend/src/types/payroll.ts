import type { Tailor } from './tailors';

export const PAYROLL_PERIOD_STATUSES = ['DRAFT', 'CALCULATED', 'FINALIZED'] as const;

export type PayrollPeriodStatus = (typeof PAYROLL_PERIOD_STATUSES)[number];

export const PAYROLL_PERIOD_STATUS_LABELS: Record<PayrollPeriodStatus, string> = {
  DRAFT: 'Draft',
  CALCULATED: 'Calculated',
  FINALIZED: 'Finalized',
};

export const PAYROLL_PERIOD_STATUS_COLORS: Record<
  PayrollPeriodStatus,
  { bg: string; text: string }
> = {
  DRAFT: { bg: '#F1F5F9', text: '#475569' },
  CALCULATED: { bg: '#EFF6FF', text: '#1E3A8A' },
  FINALIZED: { bg: '#DCFCE7', text: '#15803D' },
};

export interface PayrollPeriod {
  id: number;
  period_start: string;
  period_end: string;
  status: PayrollPeriodStatus;
  notes: string;
  created_by: number | null;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
  total_completed_pieces: number;
  total_piece_rate_earnings: number;
  total_attendance_amount: number;
  total_payable: number;
  entry_count: number;
}

export interface PayrollPeriodListResult {
  count: number;
  next: string | null;
  previous: string | null;
  results: PayrollPeriod[];
}

export interface PayrollPeriodPayload {
  period_start: string;
  period_end: string;
  notes?: string;
}

export interface PayrollEntry {
  id: number;
  payroll_period: number;
  tailor: Tailor;
  present_days: number;
  half_days: number;
  absent_days: number;
  completed_pieces: number;
  piece_rate_earnings: number;
  attendance_amount: number;
  total_payable: number;
  created_at: string;
  updated_at: string;
}

export interface PayrollEntryListResult {
  count: number;
  next: string | null;
  previous: string | null;
  results: PayrollEntry[];
}

export interface PayrollActionResponse {
  success: boolean;
  message: string;
  period: PayrollPeriod;
}

export interface PayrollCalculateResponse extends PayrollActionResponse {
  entries: PayrollEntry[];
}

export interface PayrollAssignment {
  id: number;
  order_number: string;
  garment_type: string;
  garment_code: string;
  assigned_quantity: number;
  completed_quantity: number;
  remaining_quantity: number;
  rate_per_piece_snapshot: number;
  earned_amount: number;
  status: string;
  completed_at: string | null;
}

export interface PayrollTailorDetail {
  success: boolean;
  period: PayrollPeriod;
  tailor: {
    id: number;
    name: string;
    mobile_number: string;
    is_active: boolean;
  };
  entry: PayrollEntry | null;
  assignments: PayrollAssignment[];
}
