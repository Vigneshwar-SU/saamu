import { apiClient } from './apiClient';
import type {
  ReminderCandidate,
  ReminderListData,
  ReminderListResponse,
  ReminderPrepareResponse,
} from '../types/reminders';

export const remindersService = {
  async listReminders(page = 1): Promise<ReminderListData> {
    const response = await apiClient.get<ReminderListResponse>(
      '/communications/reminders/',
      { params: { page } }
    );
    return response.data.data;
  },

  async prepareReminder(reminderId: string): Promise<ReminderCandidate> {
    const response = await apiClient.get<ReminderPrepareResponse>(
      `/communications/reminders/${reminderId}/prepare/`
    );
    return response.data.data;
  },
};
