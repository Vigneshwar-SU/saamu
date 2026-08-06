import type { PaymentType } from './billing';

export {
  PAYMENT_TYPES,
  PAYMENT_TYPE_LABELS,
} from './billing';
export type { PaymentType } from './billing';

export const EXPENSE_CATEGORIES = [
  'RENT',
  'ELECTRICITY',
  'MATERIAL',
  'MAINTENANCE',
  'SHOP_SUPPLIES',
  'TRANSPORT',
  'OTHER_EXPENSE',
] as const;

export type ExpenseCategory = (typeof EXPENSE_CATEGORIES)[number];

export const EXPENSE_CATEGORY_LABELS: Record<ExpenseCategory, string> = {
  RENT: 'Rent',
  ELECTRICITY: 'Electricity',
  MATERIAL: 'Material',
  MAINTENANCE: 'Maintenance',
  SHOP_SUPPLIES: 'Shop Supplies',
  TRANSPORT: 'Transport',
  OTHER_EXPENSE: 'Other Expense',
};

export const PAYMENT_METHODS = ['CASH', 'UPI', 'BANK_TRANSFER', 'OTHER'] as const;

export type PaymentMethod = (typeof PAYMENT_METHODS)[number];

export const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  CASH: 'Cash',
  UPI: 'UPI',
  BANK_TRANSFER: 'Bank Transfer',
  OTHER: 'Other',
};

export interface Income {
  id: number;
  payment_type: PaymentType;
  payment_type_display: string;
  payment_method: PaymentMethod;
  payment_method_display: string;
  amount: number;
  net_amount: number;
  payment_date: string;
  invoice_number: string;
  order_number: string;
  customer_name: string;
  reference: string;
  notes: string;
  recorded_by: number | null;
  recorded_by_name: string | null;
  created_at: string;
}

export interface Expense {
  id: number;
  category: ExpenseCategory;
  category_display: string;
  amount: number;
  expense_date: string;
  payment_method: PaymentMethod;
  payment_method_display: string;
  description: string;
  reference: string;
  recorded_by: number | null;
  recorded_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface FinanceListResult<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface IncomeListParams {
  date_from?: string;
  date_to?: string;
  payment_method?: PaymentMethod | '';
  payment_type?: PaymentType | '';
  page?: number;
}

export interface ExpenseListParams {
  date_from?: string;
  date_to?: string;
  category?: ExpenseCategory | '';
  payment_method?: PaymentMethod | '';
  page?: number;
}

export interface ExpensePayload {
  category: ExpenseCategory;
  amount: number;
  expense_date: string;
  payment_method: PaymentMethod;
  description?: string;
  reference?: string;
}

export interface ExpenseSummaryCategory {
  category: ExpenseCategory;
  category_display: string;
  total: number;
  count: number;
}

export interface ExpenseSummaryMethod {
  payment_method: PaymentMethod;
  payment_method_display: string;
  total: number;
  count: number;
}

export interface ExpenseSummary {
  success: boolean;
  total_expenses: number;
  expense_count: number;
  by_category: ExpenseSummaryCategory[];
  by_payment_method: ExpenseSummaryMethod[];
}

export interface ExpenseSummaryParams {
  date_from?: string;
  date_to?: string;
  category?: ExpenseCategory | '';
  payment_method?: PaymentMethod | '';
}

export interface IncomeSummaryMethod {
  payment_method: PaymentMethod;
  payment_method_display: string;
  total: number;
  count: number;
}

export interface IncomeSummaryType {
  payment_type: PaymentType;
  payment_type_display: string;
  total: number;
  count: number;
}

export interface IncomeSummary {
  success: boolean;
  total_income: number;
  payment_count: number;
  refund_count: number;
  total_refunds: number;
  by_payment_method: IncomeSummaryMethod[];
  by_payment_type: IncomeSummaryType[];
}

export interface IncomeSummaryParams {
  date_from?: string;
  date_to?: string;
  payment_method?: PaymentMethod | '';
  payment_type?: PaymentType | '';
}

export interface DashboardFinancial {
  recorded_income: number;
  recorded_expenses: number;
  net_recorded_balance: number;
  payroll_paid: number;
  salary_advances: number;
  order_revenue: number;
}

export interface DashboardOrderCounts {
  total: number;
  NEW: number;
  CUTTING: number;
  STITCHING: number;
  READY: number;
  COLLECTED: number;
  CANCELLED: number;
}

export interface DashboardWorkload {
  assigned_quantity: number;
  completed_quantity: number;
  outstanding_quantity: number;
  earned_amount: number;
}

export interface DashboardOperational {
  order_counts: DashboardOrderCounts;
  garment_quantities: Record<string, number>;
  workload: DashboardWorkload;
  active_customers: number;
  active_tailors: number;
}

export interface DashboardSummary {
  success: boolean;
  financial: DashboardFinancial;
  operational: DashboardOperational;
  recent_payments: Income[];
  recent_expenses: Expense[];
}

export interface DashboardSummaryParams {
  date_from?: string;
  date_to?: string;
}
