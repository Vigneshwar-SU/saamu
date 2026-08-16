export const ORDER_MESSAGE_TYPES = [
  'ORDER_RECEIVED',
  'ORDER_IN_PROGRESS',
  'READY_FOR_COLLECTION',
  'COLLECTED_SETTLED',
  'COLLECTED_PAYMENT_PENDING',
] as const;

export type OrderMessageType = (typeof ORDER_MESSAGE_TYPES)[number];

export const ORDER_MESSAGE_TYPE_LABELS: Record<OrderMessageType, string> = {
  ORDER_RECEIVED: 'Order Received',
  ORDER_IN_PROGRESS: 'Order In Progress',
  READY_FOR_COLLECTION: 'Ready for Collection',
  COLLECTED_SETTLED: 'Collected · Payment Settled',
  COLLECTED_PAYMENT_PENDING: 'Collected · Payment Outstanding',
};

export interface PreparedMessage {
  message_type: OrderMessageType;
  message_label: string;
  message: string;
  phone_number: string | null;
  whatsapp_url: string | null;
}

export interface PrepareMessageResponse {
  success: boolean;
  data: PreparedMessage;
}
