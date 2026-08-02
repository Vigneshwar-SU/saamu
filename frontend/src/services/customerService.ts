import { apiClient } from './apiClient';
import type {
  ApiMessageResponse,
  Customer,
  CustomerListParams,
  CustomerListResult,
  CustomerPayload,
} from '../types/customers';

export const customerService = {
  async list(params: CustomerListParams = {}): Promise<CustomerListResult> {
    const query = new URLSearchParams();
    if (params.search) query.set('search', params.search);
    if (params.status && params.status !== 'active') query.set('status', params.status);
    if (params.page && params.page > 1) query.set('page', String(params.page));
    const qs = query.toString();
    const response = await apiClient.get<CustomerListResult>(`/customers/${qs ? `?${qs}` : ''}`);
    return response.data;
  },

  async get(id: number): Promise<Customer> {
    const response = await apiClient.get<Customer>(`/customers/${id}/`);
    return response.data;
  },

  async create(payload: CustomerPayload): Promise<Customer> {
    const response = await apiClient.post<Customer>('/customers/', payload);
    return response.data;
  },

  async update(id: number, payload: CustomerPayload): Promise<Customer> {
    const response = await apiClient.patch<Customer>(`/customers/${id}/`, payload);
    return response.data;
  },

  async archive(id: number): Promise<ApiMessageResponse> {
    const response = await apiClient.post<ApiMessageResponse>(`/customers/${id}/archive/`);
    return response.data;
  },

  async restore(id: number): Promise<ApiMessageResponse> {
    const response = await apiClient.post<ApiMessageResponse>(`/customers/${id}/restore/`);
    return response.data;
  },
};
