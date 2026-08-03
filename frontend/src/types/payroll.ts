import type { Tailor } from './tailors';
import type { SalaryAdvance } from './advances';

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

export const SETTLEMENT_STATUSES = ['UNPAID', 'PARTIALLY_PAID', 'SETTLED'] as const;

export type SettlementStatus = (typeof SETTLEMENT_STATUSES)[number];

export const SETTLEMENT_STATUS_LABELS: Record<SettlementStatus, string> = {
  UNPAID: 'Unpaid',
  PARTIALLY_PAID: 'Partially Paid',
  SETTLED: 'Settled',
};

export const SETTLEMENT_STATUS_COLORS: Record<
  SettlementStatus,
  { bg: string; text: string }
> = {
  UNPAID: { bg: '#FEF3C7', text: '#B45309' },
  PARTIALLY_PAID: { bg: '#EFF6FF', text: '#1E3A8A' },
  SETTLED: { bg: '#DCFCE7', text: '#15803D' },
};

export const PAYMENT_METHODS = ['CASH', 'BANK_TRANSFER', 'UPI', 'OTHER'] as const;

export type PaymentMethod = (typeof PAYMENT_METHODS)[number];

export const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  CASH: 'Cash',
  BANK_TRANSFER: 'Bank Transfer',
  UPI: 'UPI',
  OTHER: 'Other',
};

export const SALARY_MODELS = ['PER_GARMENT', 'FIXED_SALARY', 'MIXED'] as const;

export type SalaryModel = (typeof SALARY_MODELS)[number];

export const SALARY_MODEL_LABELS: Record<SalaryModel, string> = {
  PER_GARMENT: 'Per Garment',
  FIXED_SALARY: 'Fixed Salary',
  MIXED: 'Fixed + Per Garment',
};

export interface TailorSalaryConfiguration {
  id: number;
  tailor: Tailor;
  salary_model: SalaryModel;
  salary_model_display: string;
  fixed_salary_amount: number;
  effective_from: string;
  effective_to: string | null;
  is_active: boolean;
  notes: string;
  created_by: number | null;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface TailorSalaryConfigurationListResult {
  count: number;
  next: string | null;
  previous: string | null;
  results: TailorSalaryConfiguration[];
}

export interface SalaryConfigurationPayload {
  tailor: number;
  salary_model: SalaryModel;
  fixed_salary_amount: number;
  effective_from: string;
  effective_to?: string | null;
  is_active?: boolean;
  notes?: string;
}

export interface SalaryConfigurationListParams {
  tailor?: number;
  salary_model?: SalaryModel | '';
  is_active?: boolean;
}

export interface PayrollSettlement {
  gross_payable: number;
  advance_deductions: number;
  payments_recorded: number;
  outstanding_payable: number;
  settlement_status: SettlementStatus;
  payment_count: number;
}

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
  total_fixed_salary: number;
  total_piece_rate_earnings: number;
  total_gross_salary: number;
  total_attendance_amount: number;
  total_payable: number;
  entry_count: number;
  settlement: PayrollSettlement;
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
  salary_model: SalaryModel;
  salary_model_display: string;
  fixed_salary_amount: number;
  piece_rate_earnings: number;
  gross_salary: number;
  attendance_amount: number;
  total_payable: number;
  settlement: PayrollSettlement;
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

export interface PayrollPayment {
  id: number;
  payroll_entry: number;
  tailor: Tailor;
  amount: number;
  payment_date: string;
  payment_method: PaymentMethod;
  payment_method_display: string;
  reference: string;
  notes: string;
  recorded_by: number | null;
  recorded_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaymentPayload {
  amount: number;
  payment_date: string;
  payment_method: PaymentMethod;
  reference?: string;
  notes?: string;
}

export interface SettlementResponse {
  success: boolean;
  entry: PayrollEntry;
  settlement: PayrollSettlement;
}

export interface PaymentHistoryResponse {
  success: boolean;
  entry_id: number;
  payments: PayrollPayment[];
}

export interface RecordPaymentResponse {
  success: boolean;
  message: string;
  payment: PayrollPayment;
  settlement: PayrollSettlement;
}

export interface ApplyAdvanceResponse {
  success: boolean;
  message: string;
  advance: SalaryAdvance;
  settlement: PayrollSettlement;
}

export interface SalaryBreakdown {
  salary_model: SalaryModel;
  salary_model_display: string;
  fixed_salary_amount: number;
  completed_pieces: number;
  piece_rate_earnings: number;
  gross_salary: number;
  attendance: {
    present_days: number;
    half_days: number;
    absent_days: number;
  };
}

export interface SalaryBreakdownResponse {
  success: boolean;
  period: PayrollPeriod;
  tailor: {
    id: number;
    name: string;
    mobile_number: string;
    is_active: boolean;
  };
  salary_breakdown: SalaryBreakdown | null;
  settlement: PayrollSettlement | null;
}
