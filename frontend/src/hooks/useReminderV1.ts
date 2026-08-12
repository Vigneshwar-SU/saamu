import { useQuery, useQueryClient } from '@tanstack/react-query';
import { remindersService } from '../services/remindersService';
import type { ReminderV1ListData, ReminderV1Summary } from '../types/remindersV1';

export const REMINDER_V1_LIST_KEY = 'reminder-v1-list';
export const REMINDER_V1_SUMMARY_KEY = 'reminder-v1-summary';

const NOTIFICATION_STALE_TIME = 30_000;

export const useReminderV1List = (pageSize = 200) =>
  useQuery<ReminderV1ListData>({
    queryKey: [REMINDER_V1_LIST_KEY, pageSize],
    queryFn: () => remindersService.listRemindersV1(pageSize),
    staleTime: NOTIFICATION_STALE_TIME,
  });

export const useReminderV1Summary = () =>
  useQuery<ReminderV1Summary>({
    queryKey: [REMINDER_V1_SUMMARY_KEY],
    queryFn: () => remindersService.getRemindersV1Summary(),
    staleTime: NOTIFICATION_STALE_TIME,
  });

export const invalidateRemindersV1 = (queryClient: ReturnType<typeof useQueryClient>) => {
  queryClient.invalidateQueries({ queryKey: [REMINDER_V1_LIST_KEY] });
  queryClient.invalidateQueries({ queryKey: [REMINDER_V1_SUMMARY_KEY] });
};
