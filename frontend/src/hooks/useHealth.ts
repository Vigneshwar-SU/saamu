import { useQuery } from '@tanstack/react-query';
import { fetchHealthStatus } from '../services/healthService';
import { HealthStatus } from '../types/api';

export const useHealth = () => {
  return useQuery<HealthStatus>({
    queryKey: ['health'],
    queryFn: fetchHealthStatus,
    retry: 1,
    staleTime: 30000,
  });
};
