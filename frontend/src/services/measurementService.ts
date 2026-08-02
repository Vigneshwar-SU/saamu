import { apiClient } from './apiClient';
import type { Measurement, MeasurementPayload } from '../types/customers';

export const measurementService = {
  async listForCustomer(customerId: number, currentOnly = false): Promise<Measurement[]> {
    const qs = currentOnly ? '?current=true' : '';
    const response = await apiClient.get<Measurement[]>(`/customers/${customerId}/measurements/${qs}`);
    return response.data;
  },

  async create(customerId: number, payload: MeasurementPayload): Promise<Measurement> {
    const response = await apiClient.post<Measurement>(`/customers/${customerId}/measurements/`, payload);
    return response.data;
  },

  async update(id: number, payload: MeasurementPayload): Promise<Measurement> {
    const response = await apiClient.patch<Measurement>(`/measurements/${id}/`, payload);
    return response.data;
  },
};
