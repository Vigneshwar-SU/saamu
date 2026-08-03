export const INCOME_CATEGORIES = ['ORDER_PAYMENT', 'OTHER_INCOME'] as const;

export type IncomeCategory = (typeof INCOME_CATEGORIES)[number];

export const INCOME_CATEGORY_LABELS: Record<IncomeCategory, string> = {
  ORDER_PAYMENT: 'Order Payment',
  OTHER_INCOME: 'Other Income',
};

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

export interface Income {
  id: number;
  category: IncomeCategory;
  category_display: string;
  amount: number;
  income_date: string;
  description: string;
  reference: string;
  recorded_by: number | null;
  recorded_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface Expense {
  id: number;
  category: ExpenseCategory;
  category_display: string;
  amount: number;
  expense_date: string;
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
  category?: IncomeCategory | '';
  page?: number;
}

export interface ExpenseListParams {
  date_from?: string;
  date_to?: string;
  category?: ExpenseCategory | '';
  page?: number;
}

export interface IncomePayload {
  category: IncomeCategory;
  amount: number;
  income_date: string;
  description?: string;
  reference?: string;
}

export interface ExpensePayload {
  category: ExpenseCategory;
  amount: number;
  expense_date: string;
  description?: string;
  reference?: string;
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
  recent_income: Income[];
  recent_expenses: Expense[];
}

export interface DashboardSummaryParams {
  date_from?: string;
  date_to?: string;
}
