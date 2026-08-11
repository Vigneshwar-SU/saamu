import type { Tailor } from './tailors';

export const ADVANCE_STATUSES = ['OUTSTANDING', 'DEDUCTED'] as const;

export type AdvanceStatus = (typeof ADVANCE_STATUSES)[number];

export const ADVANCE_STATUS_LABELS: Record<AdvanceStatus, string> = {
  OUTSTANDING: 'Outstanding',
  DEDUCTED: 'Deducted',
};

export const ADVANCE_STATUS_COLORS: Record<AdvanceStatus, { bg: string; text: string }> = {
  OUTSTANDING: { bg: '#FBF0E3', text: '#8F4A00' },
  DEDUCTED: { bg: '#E7E0D0', text: '#6B6B6B' },
};

export interface SalaryAdvance {
  id: number;
  tailor: Tailor;
  amount: number;
  advance_date: string;
  status: AdvanceStatus;
  notes: string;
  payroll_entry: number | null;
  deducted_at: string | null;
  recorded_by: number | null;
  recorded_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdvanceListResult {
  count: number;
  next: string | null;
  previous: string | null;
  results: SalaryAdvance[];
}

export interface AdvanceListParams {
  tailor?: number;
  status?: AdvanceStatus | '';
  date_from?: string;
  date_to?: string;
  page?: number;
}

export interface AdvancePayload {
  tailor: number;
  amount: number;
  advance_date: string;
  notes?: string;
}
