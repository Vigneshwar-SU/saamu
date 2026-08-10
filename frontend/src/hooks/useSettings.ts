import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { settingsService } from '../services/settingsService';
import { INVOICE_BILL_KEY } from './useInvoices';
import type { ShopDetails, ShopDetailsPayload } from '../types/settings';

export const SHOP_DETAILS_KEY = 'shop-details';

export const useShopDetails = () => {
  return useQuery<ShopDetails>({
    queryKey: [SHOP_DETAILS_KEY],
    queryFn: () => settingsService.getShopDetails(),
  });
};

export const useUpdateShopDetails = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ShopDetailsPayload) => settingsService.updateShopDetails(payload),
    onSuccess: (data) => {
      queryClient.setQueryData([SHOP_DETAILS_KEY], data);
      queryClient.invalidateQueries({ queryKey: [INVOICE_BILL_KEY] });
    },
  });
};
