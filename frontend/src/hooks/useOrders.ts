import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { orderService } from '../services/orderService';
import { DASHBOARD_KEY } from './useFinance';
import { REPORTS_KEY } from './useReports';
import type {
  Order,
  OrderCreatePayload,
  OrderListParams,
  OrderListResult,
  OrderStatus,
  OrderUpdatePayload,
} from '../types/orders';

export const useOrderList = (params: OrderListParams) => {
  return useQuery<OrderListResult>({
    queryKey: ['orders', params],
    queryFn: () => orderService.list(params),
  });
};

export const useOrder = (id: number) => {
  return useQuery<Order>({
    queryKey: ['order', id],
    queryFn: () => orderService.get(id),
    enabled: id > 0,
  });
};

export const useCreateOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: OrderCreatePayload) => orderService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
      queryClient.invalidateQueries({ queryKey: [REPORTS_KEY] });
    },
  });
};

export const useUpdateOrder = (id: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: OrderUpdatePayload) => orderService.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['order', id] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
      queryClient.invalidateQueries({ queryKey: [REPORTS_KEY] });
    },
  });
};

export const useChangeOrderStatus = (id: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (status: OrderStatus) => orderService.changeStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['order', id] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
      queryClient.invalidateQueries({ queryKey: [REPORTS_KEY] });
    },
  });
};
