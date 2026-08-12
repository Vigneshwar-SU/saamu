import { apiClient } from './apiClient';
import type {
  ReminderCandidate,
  ReminderListData,
  ReminderListResponse,
  ReminderPrepareResponse,
} from '../types/reminders';
import type {
  ReminderV1ListData,
  ReminderV1ListResponse,
  ReminderV1Summary,
  ReminderV1SummaryResponse,
} from '../types/remindersV1';

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

  async listRemindersV1(pageSize = 200): Promise<ReminderV1ListData> {
    const response = await apiClient.get<ReminderV1ListResponse>('/reminders/', {
      params: { page: 1, page_size: pageSize },
    });
    return response.data.data;
  },

  async getRemindersV1Summary(): Promise<ReminderV1Summary> {
    const response = await apiClient.get<ReminderV1SummaryResponse>(
      '/reminders/summary/'
    );
    return response.data.data;
  },
};
