import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { financeService } from '../services/financeService';
import type {
  DashboardSummary,
  DashboardSummaryParams,
  Expense,
  ExpenseListParams,
  ExpensePayload,
  FinanceListResult,
  Income,
  IncomeListParams,
  IncomePayload,
} from '../types/finance';

const INCOME_KEY = 'income';
const EXPENSES_KEY = 'expenses';
const DASHBOARD_KEY = 'dashboard';

export const useIncomeList = (params: IncomeListParams) => {
  return useQuery<FinanceListResult<Income>>({
    queryKey: [INCOME_KEY, params],
    queryFn: () => financeService.listIncome(params),
  });
};

export const useCreateIncome = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: IncomePayload) => financeService.createIncome(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INCOME_KEY] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
    },
  });
};

export const useExpenseList = (params: ExpenseListParams) => {
  return useQuery<FinanceListResult<Expense>>({
    queryKey: [EXPENSES_KEY, params],
    queryFn: () => financeService.listExpenses(params),
  });
};

export const useCreateExpense = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ExpensePayload) => financeService.createExpense(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [EXPENSES_KEY] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
    },
  });
};

export const useDashboardSummary = (params: DashboardSummaryParams) => {
  return useQuery<DashboardSummary>({
    queryKey: [DASHBOARD_KEY, params],
    queryFn: () => financeService.getDashboardSummary(params),
  });
};
