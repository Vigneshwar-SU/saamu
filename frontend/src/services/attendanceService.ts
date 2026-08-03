import { apiClient } from './apiClient';
import type {
  Attendance,
  AttendanceListParams,
  AttendanceListResult,
  AttendancePayload,
} from '../types/attendance';

export const attendanceService = {
  async list(params: AttendanceListParams = {}): Promise<AttendanceListResult> {
    const query = new URLSearchParams();
    if (params.tailor) query.set('tailor', String(params.tailor));
    if (params.date_from) query.set('date_from', params.date_from);
    if (params.date_to) query.set('date_to', params.date_to);
    if (params.status) query.set('status', params.status);
    if (params.page && params.page > 1) query.set('page', String(params.page));
    const qs = query.toString();
    const response = await apiClient.get<AttendanceListResult>(`/attendance/${qs ? `?${qs}` : ''}`);
    return response.data;
  },

  async create(payload: AttendancePayload): Promise<Attendance> {
    const response = await apiClient.post<Attendance>('/attendance/', payload);
    return response.data;
  },

  async update(id: number, payload: AttendancePayload): Promise<Attendance> {
    const response = await apiClient.patch<Attendance>(`/attendance/${id}/`, payload);
    return response.data;
  },
};
