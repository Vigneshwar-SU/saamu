export const ORDER_MESSAGE_TYPES = [
  'ORDER_ACKNOWLEDGEMENT',
  'ORDER_STATUS_UPDATE',
  'READY_FOR_COLLECTION',
  'PAYMENT_BALANCE',
] as const;

export type OrderMessageType = (typeof ORDER_MESSAGE_TYPES)[number];

export const ORDER_MESSAGE_TYPE_LABELS: Record<OrderMessageType, string> = {
  ORDER_ACKNOWLEDGEMENT: 'Order Acknowledgement',
  ORDER_STATUS_UPDATE: 'Order Status Update',
  READY_FOR_COLLECTION: 'Ready for Collection',
  PAYMENT_BALANCE: 'Payment / Balance Summary',
};

export interface PreparedMessage {
  message_type: OrderMessageType;
  message: string;
  phone_number: string | null;
  whatsapp_url: string | null;
}

export interface PrepareMessageResponse {
  success: boolean;
  data: PreparedMessage;
}
