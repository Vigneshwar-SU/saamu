import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { advanceService } from '../services/advanceService';
import type {
  AdvanceListParams,
  AdvanceListResult,
  AdvancePayload,
} from '../types/advances';

const ADVANCES_KEY = 'advances';

export const useAdvanceList = (params: AdvanceListParams) => {
  return useQuery<AdvanceListResult>({
    queryKey: [ADVANCES_KEY, params],
    queryFn: () => advanceService.list(params),
  });
};

export const useCreateAdvance = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AdvancePayload) => advanceService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ADVANCES_KEY] });
    },
  });
};
