import { apiClient } from './apiClient';
import type { PrepareMessageResponse, PreparedMessage } from '../types/communications';

export const communicationsService = {
  async prepareOrderMessage(orderId: number): Promise<PreparedMessage> {
    const response = await apiClient.get<PrepareMessageResponse>(
      `/communications/messages/prepare/order/${orderId}/`
    );
    return response.data.data;
  },
};
