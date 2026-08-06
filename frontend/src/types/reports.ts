import type {
  ExpenseSummaryCategory,
  ExpenseSummaryMethod,
  IncomeSummaryMethod,
  IncomeSummaryType,
} from './finance';

export interface ReportIncome {
  total_income: number;
  payment_count: number;
  refund_count: number;
  total_refunds: number;
  by_payment_method: IncomeSummaryMethod[];
  by_payment_type: IncomeSummaryType[];
}

export interface ReportExpenses {
  total_expenses: number;
  expense_count: number;
  by_category: ExpenseSummaryCategory[];
  by_payment_method: ExpenseSummaryMethod[];
}

export interface ReportOrderCounts {
  total: number;
  NEW: number;
  CUTTING: number;
  STITCHING: number;
  READY: number;
  COLLECTED: number;
  CANCELLED: number;
}

export interface ReportOrders {
  total: number;
  status_distribution: ReportOrderCounts;
  revenue: number;
  garment_quantities: Record<string, number>;
}

export interface ReportCustomers {
  active_customers: number;
  new_customers: number;
  customers_with_orders: number;
}

export interface ReportWorkload {
  assigned_quantity: number;
  completed_quantity: number;
  outstanding_quantity: number;
  earned_amount: number;
}

export interface ReportTailors {
  active_tailors: number;
  workload: ReportWorkload;
}

export interface ReportFinancial {
  income: ReportIncome;
  expenses: ReportExpenses;
  net_position: number;
  payroll_paid: number;
  salary_advances: number;
  order_revenue: number;
}

export interface ReportsSummary {
  success: boolean;
  range: {
    date_from: string | null;
    date_to: string | null;
  };
  orders: ReportOrders;
  customers: ReportCustomers;
  tailors: ReportTailors;
  financial: ReportFinancial;
}

export interface ReportsSummaryParams {
  date_from?: string;
  date_to?: string;
}
