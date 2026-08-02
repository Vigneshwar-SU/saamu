import type { Customer, GarmentType, MeasurementFieldName } from './customers';

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
  NEW: { bg: '#EFF6FF', text: '#1E3A8A' },
  CUTTING: { bg: '#FEF3C7', text: '#B45309' },
  STITCHING: { bg: '#FFEDD5', text: '#C2410C' },
  READY: { bg: '#DCFCE7', text: '#15803D' },
  COLLECTED: { bg: '#F1F5F9', text: '#475569' },
  CANCELLED: { bg: '#FEE2E2', text: '#B91C1C' },
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
