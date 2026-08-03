import { apiClient } from './apiClient';
import type {
  PayrollActionResponse,
  PayrollCalculateResponse,
  PayrollEntryListResult,
  PayrollPeriod,
  PayrollPeriodListResult,
  PayrollPeriodPayload,
  PayrollTailorDetail,
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
};
