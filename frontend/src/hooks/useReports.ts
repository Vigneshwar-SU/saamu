import { useMutation, useQuery } from '@tanstack/react-query';
import { financeService } from '../services/financeService';
import type { ReportExportResult } from '../services/financeService';
import type { ReportsSummary, ReportsSummaryParams } from '../types/reports';

export const REPORTS_KEY = 'reports';

export const useReportsSummary = (params: ReportsSummaryParams) => {
  return useQuery<ReportsSummary>({
    queryKey: [REPORTS_KEY, params],
    queryFn: () => financeService.getReportsSummary(params),
  });
};

export type ReportExportFormat = 'csv' | 'pdf';

export const useReportExport = () => {
  return useMutation<
    ReportExportResult,
    Error,
    { format: ReportExportFormat; params: ReportsSummaryParams }
  >({
    mutationFn: ({ format, params }) =>
      format === 'csv'
        ? financeService.exportReportsCsv(params)
        : financeService.exportReportsPdf(params),
  });
};
