import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { customerService } from '../services/customerService';
import { DASHBOARD_KEY } from './useFinance';
import { invalidateRemindersV1 } from './useReminderV1';
import type {
  Customer,
  CustomerListParams,
  CustomerListResult,
  CustomerPayload,
} from '../types/customers';

export const useCustomerList = (params: CustomerListParams) => {
  return useQuery<CustomerListResult>({
    queryKey: ['customers', params],
    queryFn: () => customerService.list(params),
  });
};

export const useCustomer = (id: number) => {
  return useQuery<Customer>({
    queryKey: ['customer', id],
    queryFn: () => customerService.get(id),
    enabled: id > 0,
  });
};

export const useCreateCustomer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CustomerPayload) => customerService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
      invalidateRemindersV1(queryClient);
    },
  });
};

export const useUpdateCustomer = (id: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CustomerPayload) => customerService.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      queryClient.invalidateQueries({ queryKey: ['customer', id] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
      invalidateRemindersV1(queryClient);
    },
  });
};

export const useArchiveCustomer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => customerService.archive(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      queryClient.invalidateQueries({ queryKey: ['customer', id] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
      invalidateRemindersV1(queryClient);
    },
  });
};

export const useRestoreCustomer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => customerService.restore(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      queryClient.invalidateQueries({ queryKey: ['customer', id] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
      invalidateRemindersV1(queryClient);
    },
  });
};
