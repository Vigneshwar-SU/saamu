import type { GarmentType } from './customers';

export interface Tailor {
  id: number;
  name: string;
  mobile_number: string;
  notes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TailorListResult {
  count: number;
  next: string | null;
  previous: string | null;
  results: Tailor[];
}

export type TailorScope = 'active' | 'archived' | 'all';

export interface TailorListParams {
  search?: string;
  scope?: TailorScope;
  page?: number;
}

export interface TailorPayload {
  name: string;
  mobile_number?: string;
  notes?: string;
  is_active?: boolean;
}

export interface TailorActionResponse {
  success: boolean;
  message: string;
  tailor: Tailor;
}

export interface PieceRate {
  id: number;
  garment_type: string;
  rate_per_piece: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PieceRateListResult {
  count: number;
  next: string | null;
  previous: string | null;
  results: PieceRate[];
}

export interface PieceRatePayload {
  garment_type: string;
  rate_per_piece: number;
  is_active?: boolean;
}

export const WORK_ASSIGNMENT_STATUSES = ['ASSIGNED', 'IN_PROGRESS', 'COMPLETED'] as const;

export type WorkAssignmentStatus = (typeof WORK_ASSIGNMENT_STATUSES)[number];

export const WORK_ASSIGNMENT_STATUS_LABELS: Record<WorkAssignmentStatus, string> = {
  ASSIGNED: 'Assigned',
  IN_PROGRESS: 'In Progress',
  COMPLETED: 'Completed',
};

export const WORK_ASSIGNMENT_STATUS_COLORS: Record<
  WorkAssignmentStatus,
  { bg: string; text: string }
> = {
  ASSIGNED: { bg: '#EFF6FF', text: '#1E3A8A' },
  IN_PROGRESS: { bg: '#FEF3C7', text: '#B45309' },
  COMPLETED: { bg: '#DCFCE7', text: '#15803D' },
};

export const NEXT_ASSIGNMENT_STATUS: Partial<Record<WorkAssignmentStatus, WorkAssignmentStatus>> = {
  ASSIGNED: 'IN_PROGRESS',
  IN_PROGRESS: 'COMPLETED',
};

export interface WorkAssignmentOrderItem {
  id: number;
  garment_type: string;
  garment_code: GarmentType;
  quantity: number;
  order: number;
  order_number: string;
  order_status: string;
  customer: number;
  customer_name: string;
}

export interface WorkAssignment {
  id: number;
  tailor: Tailor;
  order_item: WorkAssignmentOrderItem;
  assigned_quantity: number;
  completed_quantity: number;
  remaining_quantity: number;
  status: WorkAssignmentStatus;
  rate_per_piece_snapshot: number;
  earned_amount: number;
  assigned_at: string;
  started_at: string | null;
  completed_at: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface WorkAssignmentListResult {
  count: number;
  next: string | null;
  previous: string | null;
  results: WorkAssignment[];
}

export interface WorkAssignmentListParams {
  tailor?: number;
  order?: number;
  garment_type?: string;
  status?: WorkAssignmentStatus | '';
  date_from?: string;
  date_to?: string;
  page?: number;
}

export interface WorkAssignmentCreatePayload {
  tailor: number;
  order: number;
  order_item: number;
  assigned_quantity: number;
}

export interface WorkAssignmentStatusResponse {
  success: boolean;
  message: string;
  assignment: WorkAssignment;
}

export interface TailorEarningsBreakdownEntry {
  garment_type: string;
  completed_quantity: number;
  earned_amount: number;
}

export interface TailorWorkload {
  assigned_quantity: number;
  completed_quantity: number;
  outstanding_quantity: number;
  earned_amount: number;
}

export interface TailorEarnings {
  success: boolean;
  tailor: Tailor;
  summary: {
    total_completed_quantity: number;
    total_earned: number;
  };
  garment_breakdown: TailorEarningsBreakdownEntry[];
  workload: TailorWorkload;
}

export interface TailorSummaryEntry {
  id: number;
  name: string;
  completed_quantity: number;
  earned_amount: number;
  outstanding_quantity: number;
  workload: TailorWorkload;
}

export interface TailorEarningsSummary {
  success: boolean;
  summary: {
    total_completed_quantity: number;
    total_earned: number;
    total_active_tailors: number;
    workload: TailorWorkload & {
      total_assigned: number;
      total_completed: number;
      total_outstanding: number;
      total_earned: number;
    };
  };
  tailors: TailorSummaryEntry[];
}
