import { apiClient } from './apiClient';
import type {
  Order,
  OrderCreatePayload,
  OrderListParams,
  OrderListResult,
  OrderStatus,
  OrderStatusChangeResponse,
  OrderUpdatePayload,
  OrderWorkProgress,
  OrderWorkProgressResponse,
} from '../types/orders';

export const orderService = {
  async list(params: OrderListParams = {}): Promise<OrderListResult> {
    const query = new URLSearchParams();
    if (params.search) query.set('search', params.search);
    if (params.status) query.set('status', params.status);
    if (params.page && params.page > 1) query.set('page', String(params.page));
    if (params.dateFrom) query.set('date_from', params.dateFrom);
    if (params.dateTo) query.set('date_to', params.dateTo);
    if (params.assignable) query.set('assignable', 'true');
    const qs = query.toString();
    const response = await apiClient.get<OrderListResult>(`/orders/${qs ? `?${qs}` : ''}`);
    return response.data;
  },

  async get(id: number): Promise<Order> {
    const response = await apiClient.get<Order>(`/orders/${id}/`);
    return response.data;
  },

  async create(payload: OrderCreatePayload): Promise<Order> {
    const response = await apiClient.post<Order>('/orders/', payload);
    return response.data;
  },

  async update(id: number, payload: OrderUpdatePayload): Promise<Order> {
    const response = await apiClient.patch<Order>(`/orders/${id}/`, payload);
    return response.data;
  },

  async changeStatus(id: number, status: OrderStatus): Promise<OrderStatusChangeResponse> {
    const response = await apiClient.post<OrderStatusChangeResponse>(`/orders/${id}/status/`, {
      status,
    });
    return response.data;
  },

  async getWorkProgress(id: number): Promise<OrderWorkProgress> {
    const response = await apiClient.get<OrderWorkProgressResponse>(`/orders/${id}/work-progress/`);
    return response.data.data;
  },
};
