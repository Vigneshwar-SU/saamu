import { apiClient } from './apiClient';
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
import type {
  ReportsSummary,
  ReportsSummaryParams,
} from '../types/reports';

function buildQuery(params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      query.set(key, String(value));
    }
  });
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

export const financeService = {
  async listIncome(params: IncomeListParams = {}): Promise<FinanceListResult<Income>> {
    const response = await apiClient.get<FinanceListResult<Income>>(
      `/income/${buildQuery({ ...params })}`
    );
    return response.data;
  },

  async getIncomeSummary(params: IncomeSummaryParams = {}): Promise<IncomeSummary> {
    const response = await apiClient.get<IncomeSummary>(
      `/income/summary/${buildQuery({ ...params })}`
    );
    return response.data;
  },

  async listExpenses(params: ExpenseListParams = {}): Promise<FinanceListResult<Expense>> {
    const response = await apiClient.get<FinanceListResult<Expense>>(
      `/expenses/${buildQuery({ ...params })}`
    );
    return response.data;
  },

  async createExpense(payload: ExpensePayload): Promise<Expense> {
    const response = await apiClient.post<Expense>('/expenses/', payload);
    return response.data;
  },

  async getExpenseSummary(
    params: ExpenseSummaryParams = {}
  ): Promise<ExpenseSummary> {
    const response = await apiClient.get<ExpenseSummary>(
      `/expenses/summary/${buildQuery({ ...params })}`
    );
    return response.data;
  },

  async getDashboardSummary(
    params: DashboardSummaryParams = {}
  ): Promise<DashboardSummary> {
    const response = await apiClient.get<DashboardSummary>(
      `/dashboard/summary/${buildQuery({ ...params })}`
    );
    return response.data;
  },

  async getReportsSummary(params: ReportsSummaryParams = {}): Promise<ReportsSummary> {
    const response = await apiClient.get<ReportsSummary>(
      `/reports/summary/${buildQuery({ ...params })}`
    );
    return response.data;
  },
};
