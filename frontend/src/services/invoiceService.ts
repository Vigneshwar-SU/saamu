import { apiClient } from './apiClient';
import type {
  BillResponse,
  BillingListResult,
  CreateOrderInvoicePayload,
  CreateOrderInvoiceResponse,
  CustomerPayment,
  CustomerPaymentPayload,
  Invoice,
  InvoiceCreatePayload,
  InvoiceEligibleOrder,
  InvoiceEligibleOrderListParams,
  InvoiceListParams,
  PaymentListParams,
  RecordPaymentResponse,
} from '../types/billing';

function buildQuery(params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      query.set(key, String(value));
    }
  });
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

export const invoiceService = {
  async listInvoices(params: InvoiceListParams = {}): Promise<BillingListResult<Invoice>> {
    const response = await apiClient.get<BillingListResult<Invoice>>(
      `/invoices/${buildQuery({ ...params })}`
    );
    return response.data;
  },

  async getInvoice(id: number): Promise<Invoice> {
    const response = await apiClient.get<Invoice>(`/invoices/${id}/`);
    return response.data;
  },

  async listEligibleOrders(
    params: InvoiceEligibleOrderListParams = {}
  ): Promise<BillingListResult<InvoiceEligibleOrder>> {
    const response = await apiClient.get<BillingListResult<InvoiceEligibleOrder>>(
      `/invoices/available-orders/${buildQuery({ ...params })}`
    );
    return response.data;
  },

  async createInvoice(payload: InvoiceCreatePayload): Promise<Invoice> {
    const response = await apiClient.post<Invoice>('/invoices/', payload);
    return response.data;
  },

  async createOrderInvoice(
    orderId: number,
    payload: CreateOrderInvoicePayload = {}
  ): Promise<CreateOrderInvoiceResponse> {
    const response = await apiClient.post<CreateOrderInvoiceResponse>(
      `/orders/${orderId}/invoice/`,
      payload
    );
    return response.data;
  },

  async listPayments(
    invoiceId: number,
    params: PaymentListParams = {}
  ): Promise<BillingListResult<CustomerPayment>> {
    const response = await apiClient.get<BillingListResult<CustomerPayment>>(
      `/invoices/${invoiceId}/payments/${buildQuery({ ...params })}`
    );
    return response.data;
  },

  async createPayment(
    invoiceId: number,
    payload: CustomerPaymentPayload
  ): Promise<RecordPaymentResponse> {
    const response = await apiClient.post<RecordPaymentResponse>(
      `/invoices/${invoiceId}/payments/`,
      payload
    );
    return response.data;
  },

  async getBill(invoiceId: number): Promise<BillResponse> {
    const response = await apiClient.get<BillResponse>(`/invoices/${invoiceId}/bill/`);
    return response.data;
  },
};
