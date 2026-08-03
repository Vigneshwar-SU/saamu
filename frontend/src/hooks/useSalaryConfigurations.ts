import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { payrollService } from '../services/payrollService';
import type {
  SalaryConfigurationListParams,
  SalaryConfigurationPayload,
  TailorSalaryConfigurationListResult,
} from '../types/payroll';

const SALARY_CONFIGURATIONS_KEY = 'salary-configurations';

export const useSalaryConfigurationList = (params: SalaryConfigurationListParams = {}) => {
  return useQuery<TailorSalaryConfigurationListResult>({
    queryKey: [SALARY_CONFIGURATIONS_KEY, params],
    queryFn: () => payrollService.listSalaryConfigurations(params),
  });
};

export const useCreateSalaryConfiguration = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SalaryConfigurationPayload) =>
      payrollService.createSalaryConfiguration(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [SALARY_CONFIGURATIONS_KEY] });
      queryClient.invalidateQueries({ queryKey: ['payroll-periods'] });
    },
  });
};

export const useUpdateSalaryConfiguration = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: number;
      payload: Partial<SalaryConfigurationPayload>;
    }) => payrollService.updateSalaryConfiguration(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [SALARY_CONFIGURATIONS_KEY] });
      queryClient.invalidateQueries({ queryKey: ['payroll-periods'] });
    },
  });
};
