import { useQuery } from '@tanstack/react-query';
import { remindersService } from '../services/remindersService';
import type { ReminderListData } from '../types/reminders';

export const useReminderList = (page: number) =>
  useQuery<ReminderListData>({
    queryKey: ['reminders', page],
    queryFn: () => remindersService.listReminders(page),
  });
