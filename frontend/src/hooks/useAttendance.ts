import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { attendanceService } from '../services/attendanceService';
import type {
  AttendanceListParams,
  AttendanceListResult,
  AttendancePayload,
} from '../types/attendance';

const ATTENDANCE_KEY = 'attendance';

export const useAttendanceList = (params: AttendanceListParams) => {
  return useQuery<AttendanceListResult>({
    queryKey: [ATTENDANCE_KEY, params],
    queryFn: () => attendanceService.list(params),
  });
};

export const useCreateAttendance = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AttendancePayload) => attendanceService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ATTENDANCE_KEY] });
    },
  });
};

export const useUpdateAttendance = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: AttendancePayload }) =>
      attendanceService.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ATTENDANCE_KEY] });
    },
  });
};
