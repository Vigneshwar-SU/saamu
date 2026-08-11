import type { Customer, GarmentType, MeasurementFieldName } from './customers';
import type { OrderPaymentSummary } from './billing';

export const ORDER_STATUSES = [
  'NEW',
  'CUTTING',
  'STITCHING',
  'READY',
  'COLLECTED',
  'CANCELLED',
] as const;

export type OrderStatus = (typeof ORDER_STATUSES)[number];

export const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
  NEW: 'New',
  CUTTING: 'Cutting',
  STITCHING: 'Stitching',
  READY: 'Ready',
  COLLECTED: 'Collected',
  CANCELLED: 'Cancelled',
};

export const ORDER_STATUS_COLORS: Record<OrderStatus, { bg: string; text: string }> = {
  NEW: { bg: '#F5EBD2', text: '#7A5E0C' },
  CUTTING: { bg: '#FBF0E3', text: '#8F4A00' },
  STITCHING: { bg: '#FBF0E3', text: '#8F4A00' },
  READY: { bg: '#E7F1EA', text: '#1F5C3C' },
  COLLECTED: { bg: '#F1EDE2', text: '#6B6B6B' },
  CANCELLED: { bg: '#FBE9E6', text: '#8F2F22' },
};

export const TERMINAL_ORDER_STATUSES: ReadonlySet<OrderStatus> = new Set([
  'COLLECTED',
  'CANCELLED',
]);

export const NEXT_STATUS: Partial<Record<OrderStatus, OrderStatus>> = {
  NEW: 'CUTTING',
  CUTTING: 'STITCHING',
  STITCHING: 'READY',
  READY: 'COLLECTED',
};

export type MeasurementSnapshot = Partial<Record<MeasurementFieldName, number | null>>;

export interface OrderItem {
  id: number;
  garment_type: string;
  garment_code: GarmentType;
  quantity: number;
  assigned_quantity: number;
  remaining_quantity: number;
  measurement_id: number | null;
  measurement_version: number | null;
  measurement_snapshot: MeasurementSnapshot | null;
  unit_price: string;
  line_total: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface OrderStatusHistoryEntry {
  id: number;
  from_status: OrderStatus | null;
  to_status: OrderStatus;
  changed_by: number | null;
  changed_by_username: string | null;
  changed_at: string;
}

export interface Order {
  id: number;
  order_number: string;
  customer: Customer;
  order_date: string;
  expected_delivery_date: string | null;
  status: OrderStatus;
  notes: string;
  total_amount: string;
  collected_at: string | null;
  garment_summary: Array<{ garment_type: GarmentType; quantity: number }>;
  payment_summary: OrderPaymentSummary | null;
  items: OrderItem[];
  status_history: OrderStatusHistoryEntry[];
  created_at: string;
  updated_at: string;
}

export interface OrderListResult {
  count: number;
  next: string | null;
  previous: string | null;
  results: Order[];
}

export interface OrderListParams {
  search?: string;
  status?: OrderStatus | '';
  page?: number;
  dateFrom?: string;
  dateTo?: string;
}

export interface OrderItemPayload {
  garment_type: GarmentType;
  quantity: number;
  unit_price: string;
  measurement_id: number;
  notes?: string;
}

export interface OrderCreatePayload {
  customer: number;
  order_date?: string;
  expected_delivery_date?: string | null;
  notes?: string;
  items: OrderItemPayload[];
}

export interface OrderUpdatePayload {
  notes?: string;
  expected_delivery_date?: string | null;
}

export interface OrderStatusChangeResponse {
  success: boolean;
  message: string;
  order: Order;
}
