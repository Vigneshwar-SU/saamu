import { apiClient } from './apiClient';
import type {
  ApplyAdvanceResponse,
  PaymentHistoryResponse,
  PaymentPayload,
  PayrollActionResponse,
  PayrollCalculateResponse,
  PayrollEntryListResult,
  PayrollPeriod,
  PayrollPeriodListResult,
  PayrollPeriodPayload,
  PayrollTailorDetail,
  RecordPaymentResponse,
  SalaryConfigurationListParams,
  SalaryConfigurationPayload,
  SettlementResponse,
  TailorSalaryConfiguration,
  TailorSalaryConfigurationListResult,
} from '../types/payroll';

export const payrollService = {
  async listPeriods(): Promise<PayrollPeriodListResult> {
    const response = await apiClient.get<PayrollPeriodListResult>('/payroll/periods/');
    return response.data;
  },

  async getPeriod(id: number): Promise<PayrollPeriod> {
    const response = await apiClient.get<PayrollPeriod>(`/payroll/periods/${id}/`);
    return response.data;
  },

  async createPeriod(payload: PayrollPeriodPayload): Promise<PayrollPeriod> {
    const response = await apiClient.post<PayrollPeriod>('/payroll/periods/', payload);
    return response.data;
  },

  async calculate(id: number): Promise<PayrollCalculateResponse> {
    const response = await apiClient.post<PayrollCalculateResponse>(`/payroll/periods/${id}/calculate/`);
    return response.data;
  },

  async finalize(id: number): Promise<PayrollActionResponse> {
    const response = await apiClient.post<PayrollActionResponse>(`/payroll/periods/${id}/finalize/`);
    return response.data;
  },

  async listEntries(params: { period?: number; tailor?: number } = {}): Promise<PayrollEntryListResult> {
    const query = new URLSearchParams();
    if (params.period) query.set('period', String(params.period));
    if (params.tailor) query.set('tailor', String(params.tailor));
    const qs = query.toString();
    const response = await apiClient.get<PayrollEntryListResult>(
      `/payroll/entries/${qs ? `?${qs}` : ''}`
    );
    return response.data;
  },

  async tailorDetail(periodId: number, tailorId: number): Promise<PayrollTailorDetail> {
    const response = await apiClient.get<PayrollTailorDetail>(
      `/payroll/periods/${periodId}/tailors/${tailorId}/`
    );
    return response.data;
  },

  async getSettlement(entryId: number): Promise<SettlementResponse> {
    const response = await apiClient.get<SettlementResponse>(
      `/payroll/entries/${entryId}/settlement/`
    );
    return response.data;
  },

  async listPayments(entryId: number): Promise<PaymentHistoryResponse> {
    const response = await apiClient.get<PaymentHistoryResponse>(
      `/payroll/entries/${entryId}/payments/`
    );
    return response.data;
  },

  async recordPayment(entryId: number, payload: PaymentPayload): Promise<RecordPaymentResponse> {
    const response = await apiClient.post<RecordPaymentResponse>(
      `/payroll/entries/${entryId}/payments/`,
      payload
    );
    return response.data;
  },

  async settleEntry(entryId: number, payload: PaymentPayload): Promise<RecordPaymentResponse> {
    const response = await apiClient.post<RecordPaymentResponse>(
      `/payroll/entries/${entryId}/settle/`,
      payload
    );
    return response.data;
  },

  async applyAdvance(entryId: number, advanceId: number): Promise<ApplyAdvanceResponse> {
    const response = await apiClient.post<ApplyAdvanceResponse>(
      `/payroll/entries/${entryId}/apply-advance/`,
      { advance_id: advanceId }
    );
    return response.data;
  },

  async listSalaryConfigurations(
    params: SalaryConfigurationListParams = {}
  ): Promise<TailorSalaryConfigurationListResult> {
    const query = new URLSearchParams();
    if (params.tailor) query.set('tailor', String(params.tailor));
    if (params.salary_model) query.set('salary_model', params.salary_model);
    if (params.is_active !== undefined) query.set('is_active', String(params.is_active));
    const qs = query.toString();
    const response = await apiClient.get<TailorSalaryConfigurationListResult>(
      `/salary-configurations/${qs ? `?${qs}` : ''}`
    );
    return response.data;
  },

  async createSalaryConfiguration(
    payload: SalaryConfigurationPayload
  ): Promise<TailorSalaryConfiguration> {
    const response = await apiClient.post<TailorSalaryConfiguration>(
      '/salary-configurations/',
      payload
    );
    return response.data;
  },

  async updateSalaryConfiguration(
    id: number,
    payload: Partial<SalaryConfigurationPayload>
  ): Promise<TailorSalaryConfiguration> {
    const response = await apiClient.patch<TailorSalaryConfiguration>(
      `/salary-configurations/${id}/`,
      payload
    );
    return response.data;
  },
};
