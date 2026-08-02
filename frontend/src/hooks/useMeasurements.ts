import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { measurementService } from '../services/measurementService';
import type { Measurement, MeasurementPayload } from '../types/customers';

export const useMeasurements = (customerId: number, currentOnly = false) => {
  return useQuery<Measurement[]>({
    queryKey: ['measurements', customerId, currentOnly],
    queryFn: () => measurementService.listForCustomer(customerId, currentOnly),
    enabled: customerId > 0,
  });
};

export const useCreateMeasurement = (customerId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: MeasurementPayload) =>
      measurementService.create(customerId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['measurements', customerId] });
    },
  });
};

export const useUpdateMeasurement = (customerId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: MeasurementPayload }) =>
      measurementService.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['measurements', customerId] });
    },
  });
};
