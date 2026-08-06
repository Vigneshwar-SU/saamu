import { useQuery } from '@tanstack/react-query';
import { financeService } from '../services/financeService';
import type { ReportsSummary, ReportsSummaryParams } from '../types/reports';

export const REPORTS_KEY = 'reports';

export const useReportsSummary = (params: ReportsSummaryParams) => {
  return useQuery<ReportsSummary>({
    queryKey: [REPORTS_KEY, params],
    queryFn: () => financeService.getReportsSummary(params),
  });
};
