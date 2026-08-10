import { apiClient } from './apiClient';
import type { ShopDetails, ShopDetailsPayload } from '../types/settings';

export const settingsService = {
  async getShopDetails(): Promise<ShopDetails> {
    const response = await apiClient.get<ShopDetails>('/settings/shop-details/');
    return response.data;
  },

  async updateShopDetails(payload: ShopDetailsPayload): Promise<ShopDetails> {
    const response = await apiClient.put<ShopDetails>('/settings/shop-details/', payload);
    return response.data;
  },
};
