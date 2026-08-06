import type { OrderStatus } from './orders';

export const REMINDER_TYPES = [
  'READY_FOR_COLLECTION',
  'BALANCE_OUTSTANDING',
] as const;

export type ReminderType = (typeof REMINDER_TYPES)[number];

export const REMINDER_TYPE_LABELS: Record<ReminderType, string> = {
  READY_FOR_COLLECTION: 'Ready for Collection',
  BALANCE_OUTSTANDING: 'Balance Outstanding',
};

export interface ReminderEligibility {
  eligible: boolean;
  code: string;
  message: string;
}

export interface ReminderCandidate {
  id: string;
  reminder_type: ReminderType;
  reminder_type_label: string;
  order: { id: number; order_number: string; status: OrderStatus };
  customer: { id: number; full_name: string };
  eligibility: ReminderEligibility;
  message: string;
  phone_number: string | null;
  whatsapp_url: string | null;
}

export interface ReminderListData {
  count: number;
  next: string | null;
  previous: string | null;
  results: ReminderCandidate[];
}

export interface ReminderListResponse {
  success: boolean;
  data: ReminderListData;
}

export interface ReminderPrepareResponse {
  success: boolean;
  data: ReminderCandidate;
}
