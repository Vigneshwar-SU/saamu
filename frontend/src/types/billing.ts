import type { Customer } from './customers';

export const INVOICE_STATUSES = ['UNPAID', 'PARTIALLY_PAID', 'PAID'] as const;

export type InvoiceStatus = (typeof INVOICE_STATUSES)[number];

export const INVOICE_STATUS_LABELS: Record<InvoiceStatus, string> = {
  UNPAID: 'Unpaid',
  PARTIALLY_PAID: 'Partially Paid',
  PAID: 'Paid',
};

export const INVOICE_STATUS_COLORS: Record<InvoiceStatus, { bg: string; text: string }> = {
  UNPAID: { bg: '#FEE2E2', text: '#B91C1C' },
  PARTIALLY_PAID: { bg: '#FEF3C7', text: '#B45309' },
  PAID: { bg: '#DCFCE7', text: '#15803D' },
};

export const PAYMENT_METHODS = ['CASH', 'UPI', 'BANK_TRANSFER', 'OTHER'] as const;

export type PaymentMethod = (typeof PAYMENT_METHODS)[number];

export const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  CASH: 'Cash',
  UPI: 'UPI',
  BANK_TRANSFER: 'Bank Transfer',
  OTHER: 'Other',
};

export const PAYMENT_TYPES = ['ADVANCE', 'PARTIAL', 'FINAL', 'REFUND'] as const;

export type PaymentType = (typeof PAYMENT_TYPES)[number];

export const PAYMENT_TYPE_LABELS: Record<PaymentType, string> = {
  ADVANCE: 'Advance',
  PARTIAL: 'Partial',
  FINAL: 'Final',
  REFUND: 'Refund',
};

export interface InvoiceItem {
  id: number;
  garment_type: string;
  garment_code: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

export interface InvoiceOrder {
  id: number;
  order_number: string;
  order_date: string;
  status: string;
  total_amount: number;
}

export interface Invoice {
  id: number;
  invoice_number: string;
  invoice_date: string;
  customer: Customer;
  order: InvoiceOrder;
  items: InvoiceItem[];
  subtotal: number;
  adjustment_amount: number;
  total_amount: number;
  gross_paid: number;
  refunded_amount: number;
  amount_paid: number;
  balance_due: number;
  status: InvoiceStatus;
  payment_count: number;
  notes: string;
  created_by: number | null;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerPayment {
  id: number;
  invoice: number;
  invoice_number: string;
  payment_type: PaymentType;
  payment_type_display: string;
  refunded_payment: number | null;
  amount: number;
  payment_date: string;
  payment_method: PaymentMethod;
  payment_method_display: string;
  reference: string;
  notes: string;
  recorded_by: number | null;
  recorded_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface BillingListResult<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface InvoiceListParams {
  search?: string;
  customer?: number | '';
  order?: number | '';
  status?: InvoiceStatus | '';
  date_from?: string;
  date_to?: string;
  page?: number;
}

export interface InvoiceCreatePayload {
  order: number;
  invoice_date?: string;
  notes?: string;
}

export interface CreateOrderInvoicePayload {
  invoice_date?: string;
  notes?: string;
}

export interface CustomerPaymentPayload {
  amount: number;
  payment_date?: string;
  payment_method: PaymentMethod;
  payment_type?: PaymentType;
  refunded_payment?: number | null;
  reference?: string;
  notes?: string;
}

export interface PaymentListParams {
  payment_method?: PaymentMethod | '';
  date_from?: string;
  date_to?: string;
  page?: number;
}

export interface RecordPaymentResponse {
  success: boolean;
  message: string;
  payment: CustomerPayment;
  invoice: Invoice;
}

export interface CreateOrderInvoiceResponse {
  success: boolean;
  message: string;
  invoice: Invoice;
}

export interface BillShop {
  name: string;
  tagline: string;
  address: string;
  phone: string;
  established_year: number;
}

export interface BillMetadata {
  invoice_number: string;
  invoice_date: string;
  generated_at: string;
}

export interface BillCustomer {
  full_name: string;
  mobile_number: string;
}

export interface BillOrder {
  order_number: string;
  order_date: string;
  expected_delivery_date: string | null;
  status: string;
}

export interface BillGarment {
  garment_type: string;
  garment_code: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

export interface BillPayment {
  id: number;
  payment_type: PaymentType;
  payment_type_display: string;
  amount: number;
  payment_date: string;
  payment_method: PaymentMethod;
  payment_method_display: string;
  reference: string;
  notes: string;
  recorded_by: string | null;
}

export interface BillTotals {
  subtotal: number;
  adjustment_amount: number;
  total_amount: number;
  gross_paid: number;
  refunded_amount: number;
  amount_paid: number;
  balance_due: number;
  status: InvoiceStatus;
}

export interface Bill {
  shop: BillShop;
  bill_metadata: BillMetadata;
  customer: BillCustomer;
  order: BillOrder;
  garments: BillGarment[];
  payment_history: BillPayment[];
  totals: BillTotals;
}

export interface BillResponse {
  success: boolean;
  bill: Bill;
}

export interface OrderPaymentSummary {
  order_total: number;
  total_paid: number;
  outstanding_balance: number;
  payment_status: InvoiceStatus;
  payment_count: number;
  refunded_amount: number;
  has_invoice: boolean;
}
