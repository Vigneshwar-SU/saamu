import { apiClient } from './apiClient';
import type {
  OrderMessageType,
  PrepareMessageResponse,
  PreparedMessage,
} from '../types/communications';

export const communicationsService = {
  async prepareOrderMessage(
    orderId: number,
    messageType: OrderMessageType
  ): Promise<PreparedMessage> {
    const response = await apiClient.get<PrepareMessageResponse>(
      `/communications/messages/prepare/order/${orderId}/`,
      { params: { message_type: messageType } }
    );
    return response.data.data;
  },
};
