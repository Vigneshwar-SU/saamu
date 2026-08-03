import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { payrollService } from '../services/payrollService';
import type {
  PaymentHistoryResponse,
  PaymentPayload,
  PayrollEntryListResult,
  PayrollPeriod,
  PayrollPeriodPayload,
  PayrollTailorDetail,
  SettlementResponse,
} from '../types/payroll';

const PAYROLL_PERIODS_KEY = 'payroll-periods';
const PAYROLL_ENTRIES_KEY = 'payroll-entries';
const PAYMENT_HISTORY_KEY = 'payroll-payment-history';

export const usePayrollPeriodList = () => {
  return useQuery({
    queryKey: [PAYROLL_PERIODS_KEY],
    queryFn: () => payrollService.listPeriods(),
  });
};

export const usePayrollPeriod = (id: number) => {
  return useQuery<PayrollPeriod>({
    queryKey: [PAYROLL_PERIODS_KEY, id],
    queryFn: () => payrollService.getPeriod(id),
    enabled: id > 0,
  });
};

export const useCreatePayrollPeriod = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PayrollPeriodPayload) => payrollService.createPeriod(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PAYROLL_PERIODS_KEY] });
    },
  });
};

export const useCalculatePayrollPeriod = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => payrollService.calculate(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: [PAYROLL_PERIODS_KEY] });
      queryClient.invalidateQueries({ queryKey: [PAYROLL_PERIODS_KEY, id] });
      queryClient.invalidateQueries({ queryKey: [PAYROLL_ENTRIES_KEY] });
    },
  });
};

export const useFinalizePayrollPeriod = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => payrollService.finalize(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: [PAYROLL_PERIODS_KEY] });
      queryClient.invalidateQueries({ queryKey: [PAYROLL_PERIODS_KEY, id] });
    },
  });
};

export const usePayrollEntries = (params: { period?: number; tailor?: number }) => {
  return useQuery<PayrollEntryListResult>({
    queryKey: [PAYROLL_ENTRIES_KEY, params],
    queryFn: () => payrollService.listEntries(params),
    enabled: !!params.period,
  });
};

export const usePayrollTailorDetail = (periodId: number, tailorId: number) => {
  return useQuery<PayrollTailorDetail>({
    queryKey: ['payroll-tailor-detail', periodId, tailorId],
    queryFn: () => payrollService.tailorDetail(periodId, tailorId),
    enabled: periodId > 0 && tailorId > 0,
  });
};

export const usePayrollSettlement = (entryId: number) => {
  return useQuery<SettlementResponse>({
    queryKey: ['payroll-settlement', entryId],
    queryFn: () => payrollService.getSettlement(entryId),
    enabled: entryId > 0,
  });
};

export const usePayrollPaymentHistory = (entryId: number) => {
  return useQuery<PaymentHistoryResponse>({
    queryKey: [PAYMENT_HISTORY_KEY, entryId],
    queryFn: () => payrollService.listPayments(entryId),
    enabled: entryId > 0,
  });
};

export const useRecordPayment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ entryId, payload }: { entryId: number; payload: PaymentPayload }) =>
      payrollService.recordPayment(entryId, payload),
    onSuccess: (_data, { entryId }) => {
      queryClient.invalidateQueries({ queryKey: [PAYROLL_ENTRIES_KEY] });
      queryClient.invalidateQueries({ queryKey: ['payroll-settlement', entryId] });
      queryClient.invalidateQueries({ queryKey: [PAYMENT_HISTORY_KEY, entryId] });
    },
  });
};

export const useSettleEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ entryId, payload }: { entryId: number; payload: PaymentPayload }) =>
      payrollService.settleEntry(entryId, payload),
    onSuccess: (_data, { entryId }) => {
      queryClient.invalidateQueries({ queryKey: [PAYROLL_ENTRIES_KEY] });
      queryClient.invalidateQueries({ queryKey: ['payroll-settlement', entryId] });
      queryClient.invalidateQueries({ queryKey: [PAYMENT_HISTORY_KEY, entryId] });
    },
  });
};

export const useApplyAdvanceToEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ entryId, advanceId }: { entryId: number; advanceId: number }) =>
      payrollService.applyAdvance(entryId, advanceId),
    onSuccess: (_data, { entryId }) => {
      queryClient.invalidateQueries({ queryKey: [PAYROLL_ENTRIES_KEY] });
      queryClient.invalidateQueries({ queryKey: ['payroll-settlement', entryId] });
      queryClient.invalidateQueries({ queryKey: [PAYMENT_HISTORY_KEY, entryId] });
      queryClient.invalidateQueries({ queryKey: ['advances'] });
    },
  });
};
