import { apiClient } from './apiClient';
import { HealthStatus } from '../types/api';

export const fetchHealthStatus = async (): Promise<HealthStatus> => {
  const response = await apiClient.get<HealthStatus>('/health/');
  return response.data;
};
