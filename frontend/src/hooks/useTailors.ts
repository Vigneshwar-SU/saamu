import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { DASHBOARD_KEY } from './useFinance';
import { REPORTS_KEY } from './useReports';
import { invalidateRemindersV1 } from './useReminderV1';
import { pieceRateService, tailorService, workAssignmentService } from '../services/tailorService';
import type {
  PieceRatePayload,
  Tailor,
  TailorEarnings,
  TailorEarningsSummary,
  TailorListParams,
  TailorListResult,
  TailorPayload,
  WorkAssignmentCreatePayload,
  WorkAssignmentListParams,
  WorkAssignmentListResult,
  WorkAssignmentStatus,
} from '../types/tailors';

const TAILORS_KEY = 'tailors';
const PIECE_RATES_KEY = 'piece-rates';
const WORK_ASSIGNMENTS_KEY = 'work-assignments';
const EARNINGS_SUMMARY_KEY = 'tailor-earnings-summary';
const EARNINGS_KEY = 'tailor-earnings';

const invalidateEarnings = (queryClient: ReturnType<typeof useQueryClient>) => {
  queryClient.invalidateQueries({ queryKey: [EARNINGS_SUMMARY_KEY] });
  queryClient.invalidateQueries({ queryKey: [EARNINGS_KEY] });
};

export const useTailorList = (params: TailorListParams) => {
  return useQuery<TailorListResult>({
    queryKey: [TAILORS_KEY, params],
    queryFn: () => tailorService.list(params),
  });
};

export const useTailor = (id: number) => {
  return useQuery<Tailor>({
    queryKey: ['tailor', id],
    queryFn: () => tailorService.get(id),
    enabled: id > 0,
  });
};

export const useCreateTailor = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TailorPayload) => tailorService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TAILORS_KEY] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
      invalidateRemindersV1(queryClient);
    },
  });
};

export const useUpdateTailor = (id: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TailorPayload) => tailorService.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TAILORS_KEY] });
      queryClient.invalidateQueries({ queryKey: ['tailor', id] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
      invalidateRemindersV1(queryClient);
    },
  });
};

export const useArchiveTailor = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => tailorService.archive(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: [TAILORS_KEY] });
      queryClient.invalidateQueries({ queryKey: ['tailor', id] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
      invalidateRemindersV1(queryClient);
    },
  });
};

export const useRestoreTailor = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => tailorService.restore(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: [TAILORS_KEY] });
      queryClient.invalidateQueries({ queryKey: ['tailor', id] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
      invalidateRemindersV1(queryClient);
    },
  });
};

export const usePieceRates = () => {
  return useQuery({
    queryKey: [PIECE_RATES_KEY],
    queryFn: () => pieceRateService.list(),
  });
};

export const useCreatePieceRate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PieceRatePayload) => pieceRateService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PIECE_RATES_KEY] });
    },
  });
};

export const useUpdatePieceRate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<PieceRatePayload> }) =>
      pieceRateService.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PIECE_RATES_KEY] });
    },
  });
};

export const useWorkAssignmentList = (params: WorkAssignmentListParams) => {
  return useQuery<WorkAssignmentListResult>({
    queryKey: [WORK_ASSIGNMENTS_KEY, params],
    queryFn: () => workAssignmentService.list(params),
  });
};

export const useCreateWorkAssignment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: WorkAssignmentCreatePayload) => workAssignmentService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [WORK_ASSIGNMENTS_KEY] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['order'] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
      queryClient.invalidateQueries({ queryKey: [REPORTS_KEY] });
      invalidateEarnings(queryClient);
      invalidateRemindersV1(queryClient);
    },
  });
};

export const useUpdateWorkAssignment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, completedQuantity }: { id: number; completedQuantity: number }) =>
      workAssignmentService.reportProgress(id, completedQuantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [WORK_ASSIGNMENTS_KEY] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
      queryClient.invalidateQueries({ queryKey: [REPORTS_KEY] });
      invalidateEarnings(queryClient);
      invalidateRemindersV1(queryClient);
    },
  });
};

export const useChangeWorkAssignmentStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      status,
      completedQuantity,
    }: {
      id: number;
      status: WorkAssignmentStatus;
      completedQuantity?: number;
    }) => workAssignmentService.changeStatus(id, status, completedQuantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [WORK_ASSIGNMENTS_KEY] });
      queryClient.invalidateQueries({ queryKey: [DASHBOARD_KEY] });
      queryClient.invalidateQueries({ queryKey: [REPORTS_KEY] });
      invalidateEarnings(queryClient);
      invalidateRemindersV1(queryClient);
    },
  });
};

export const useTailorEarnings = (
  id: number,
  params: { date_from?: string; date_to?: string } = {}
) => {
  return useQuery<TailorEarnings>({
    queryKey: [EARNINGS_KEY, id, params],
    queryFn: () => tailorService.earnings(id, params),
    enabled: id > 0,
  });
};

export const useTailorEarningsSummary = () => {
  return useQuery<TailorEarningsSummary>({
    queryKey: [EARNINGS_SUMMARY_KEY],
    queryFn: () => tailorService.earningsSummary(),
  });
};
