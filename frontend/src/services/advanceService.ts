import { apiClient } from './apiClient';
import type {
  AdvanceListParams,
  AdvanceListResult,
  AdvancePayload,
  SalaryAdvance,
} from '../types/advances';

export const advanceService = {
  async list(params: AdvanceListParams = {}): Promise<AdvanceListResult> {
    const query = new URLSearchParams();
    if (params.tailor) query.set('tailor', String(params.tailor));
    if (params.status) query.set('status', params.status);
    if (params.date_from) query.set('date_from', params.date_from);
    if (params.date_to) query.set('date_to', params.date_to);
    if (params.page) query.set('page', String(params.page));
    const qs = query.toString();
    const response = await apiClient.get<AdvanceListResult>(
      `/advances/${qs ? `?${qs}` : ''}`
    );
    return response.data;
  },

  async get(id: number): Promise<SalaryAdvance> {
    const response = await apiClient.get<SalaryAdvance>(`/advances/${id}/`);
    return response.data;
  },

  async create(payload: AdvancePayload): Promise<SalaryAdvance> {
    const response = await apiClient.post<SalaryAdvance>('/advances/', payload);
    return response.data;
  },
};
