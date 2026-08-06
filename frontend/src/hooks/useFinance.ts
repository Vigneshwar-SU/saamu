import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { financeService } from '../services/financeService';
import { REPORTS_KEY } from './useReports';
import type {
  DashboardSummary,
  DashboardSummaryParams,
  Expense,
  ExpenseListParams,
  ExpensePayload,
  ExpenseSummary,
  ExpenseSummaryParams,
  FinanceListResult,
  Income,
  IncomeListParams,
  IncomeSummary,
  IncomeSummaryParams,
} from '../types/finance';

export const INCOME_KEY = 'income';
export const INCOME_SUMMARY_KEY = 'income-summary';
export const EXPENSES_KEY = 'expenses';
export const EXPENSE_SUMMARY_KEY = 'expense-summary';
export const DASHBOARD_KEY = 'dashboard';

export const useIncomeList = (params: IncomeListParams) => {
  return useQuery<FinanceListResult<Income>>({
    queryKey: [INCOME_KEY, params],
    queryFn: () => financeService.listIncome(params),
  });
};

export const useIncomeSummary = (params: IncomeSummaryParams) => {
  return useQuery<IncomeSummary>({
    queryKey: [INCOME_SUMMARY_KEY, params],
    queryFn: () => financeService.getIncomeSummary(params),
  });
};

export const useExpenseList = (params: ExpenseListParams) => {
  return useQuery<FinanceListResult<Expense>>({
    queryKey: [EXPENSES_KEY, params],
    queryFn: () => financeService.listExpenses(params),
  });
};

export const useExpenseSummary = (params: ExpenseSummaryParams) => {
  return useQuery<ExpenseSummary>({
    queryKey: [EXPENSE_SUMMARY_KEY, params],
    queryFn: () => financeService.getExpenseSummary(params),
  });
};

export const useCreateExpense = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ExpensePayload) => financeService.createExpense(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [EXPENSES_KEY] });
      queryClient.invalidateQueries({ queryKey: [EXPENSE_SUMMARY_KEY] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
      queryClient.invalidateQueries({ queryKey: [REPORTS_KEY] });
    },
  });
};

export const useDashboardSummary = (params: DashboardSummaryParams) => {
  return useQuery<DashboardSummary>({
    queryKey: [DASHBOARD_KEY, params],
    queryFn: () => financeService.getDashboardSummary(params),
  });
};
