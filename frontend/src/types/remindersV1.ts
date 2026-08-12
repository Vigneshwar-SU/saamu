import type { OrderStatus } from './orders';

export const REMINDER_V1_TYPES = [
  'OVERDUE_ORDER',
  'ORDER_DUE_TODAY',
  'ORDER_DUE_TOMORROW',
  'READY_FOR_PICKUP',
  'PAYMENT_OUTSTANDING',
  'TAILOR_WORKLOAD',
  'MEASUREMENT_MISSING',
  'CUSTOMER_FOLLOW_UP',
  'MANUAL_REMINDER',
] as const;

export type ReminderV1Type = (typeof REMINDER_V1_TYPES)[number];

export const REMINDER_V1_CATEGORIES = [
  'orders',
  'payments',
  'tailors',
  'customers',
  'manual',
] as const;

export type ReminderV1Category = (typeof REMINDER_V1_CATEGORIES)[number];

export interface ReminderV1OrderContext {
  id: number;
  order_number: string;
  status: OrderStatus;
  status_label: string;
  expected_delivery_date: string | null;
}

export interface ReminderV1CustomerContext {
  id: number;
  full_name: string;
}

export interface ReminderV1TailorContext {
  id: number;
  full_name: string;
  outstanding_quantity: number;
}

export type ReminderV1ActionKind = 'order' | 'tailor' | 'customer' | 'manual';

export interface ReminderV1Action {
  kind: ReminderV1ActionKind;
  target_id: number;
  label: string;
}

export interface ReminderV1Candidate {
  id: string;
  reminder_type: ReminderV1Type;
  reminder_type_label: string;
  category: ReminderV1Category;
  date: string | null;
  priority: string | null;
  title: string;
  description: string;
  order: ReminderV1OrderContext | null;
  customer: ReminderV1CustomerContext | null;
  tailor: ReminderV1TailorContext | null;
  action: ReminderV1Action;
  message: string | null;
  phone_number: string | null;
  whatsapp_url: string | null;
  is_manual: boolean;
}

export interface ReminderV1Summary {
  total: number;
  by_type: Record<ReminderV1Type, number>;
  by_category: Record<ReminderV1Category, number>;
}

export interface ReminderV1ListData {
  count: number;
  next: string | null;
  previous: string | null;
  results: ReminderV1Candidate[];
}

export interface ReminderV1ListResponse {
  success: boolean;
  data: ReminderV1ListData;
}

export interface ReminderV1SummaryResponse {
  success: boolean;
  data: ReminderV1Summary;
}
