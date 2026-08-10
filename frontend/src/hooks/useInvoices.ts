import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { invoiceService } from '../services/invoiceService';
import {
  DASHBOARD_KEY,
  INCOME_KEY,
  INCOME_SUMMARY_KEY,
} from './useFinance';
import { REPORTS_KEY } from './useReports';
import type {
  BillResponse,
  BillingListResult,
  CreateOrderInvoicePayload,
  CustomerPayment,
  CustomerPaymentPayload,
  Invoice,
  InvoiceCreatePayload,
  InvoiceEligibleOrder,
  InvoiceEligibleOrderListParams,
  InvoiceListParams,
  PaymentListParams,
} from '../types/billing';

const INVOICES_KEY = 'invoices';
const INVOICE_PAYMENTS_KEY = 'invoice-payments';
const INVOICE_ELIGIBLE_ORDERS_KEY = 'invoice-eligible-orders';
export const INVOICE_BILL_KEY = 'invoice-bill';

export const useInvoiceList = (params: InvoiceListParams, enabled = true) => {
  return useQuery<BillingListResult<Invoice>>({
    queryKey: [INVOICES_KEY, params],
    queryFn: () => invoiceService.listInvoices(params),
    enabled,
  });
};

export const useInvoice = (id: number) => {
  return useQuery<Invoice>({
    queryKey: [INVOICES_KEY, id],
    queryFn: () => invoiceService.getInvoice(id),
    enabled: id > 0,
  });
};

export const useInvoiceEligibleOrders = (
  params: InvoiceEligibleOrderListParams = {}
) => {
  return useQuery<BillingListResult<InvoiceEligibleOrder>>({
    queryKey: [INVOICE_ELIGIBLE_ORDERS_KEY, params],
    queryFn: () => invoiceService.listEligibleOrders(params),
  });
};

export const useCreateInvoice = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: InvoiceCreatePayload) => invoiceService.createInvoice(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INVOICES_KEY] });
      queryClient.invalidateQueries({ queryKey: [INVOICE_ELIGIBLE_ORDERS_KEY] });
      queryClient.invalidateQueries({ queryKey: ['order'] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: [REPORTS_KEY] });
    },
  });
};

export const useCreateOrderInvoice = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      orderId,
      payload,
    }: {
      orderId: number;
      payload: CreateOrderInvoicePayload;
    }) => invoiceService.createOrderInvoice(orderId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INVOICES_KEY] });
      queryClient.invalidateQueries({ queryKey: [INVOICE_ELIGIBLE_ORDERS_KEY] });
      queryClient.invalidateQueries({ queryKey: ['order'] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: [REPORTS_KEY] });
    },
  });
};

export const useInvoicePayments = (invoiceId: number, params: PaymentListParams = {}) => {
  return useQuery<BillingListResult<CustomerPayment>>({
    queryKey: [INVOICE_PAYMENTS_KEY, invoiceId, params],
    queryFn: () => invoiceService.listPayments(invoiceId, params),
    enabled: invoiceId > 0,
  });
};

export const useCreatePayment = (invoiceId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CustomerPaymentPayload) =>
      invoiceService.createPayment(invoiceId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INVOICES_KEY] });
      queryClient.invalidateQueries({ queryKey: [INVOICE_PAYMENTS_KEY, invoiceId] });
      queryClient.invalidateQueries({ queryKey: [INVOICE_BILL_KEY, invoiceId] });
      queryClient.invalidateQueries({ queryKey: [INCOME_KEY] });
      queryClient.invalidateQueries({ queryKey: [INCOME_SUMMARY_KEY] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
      queryClient.invalidateQueries({ queryKey: [REPORTS_KEY] });
    },
  });
};

export const useInvoiceBill = (invoiceId: number) => {
  return useQuery<BillResponse>({
    queryKey: [INVOICE_BILL_KEY, invoiceId],
    queryFn: () => invoiceService.getBill(invoiceId),
    enabled: invoiceId > 0,
  });
};
