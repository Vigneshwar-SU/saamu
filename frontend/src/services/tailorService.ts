import { apiClient } from './apiClient';
import type {
  PieceRate,
  PieceRateListResult,
  PieceRatePayload,
  Tailor,
  TailorActionResponse,
  TailorEarnings,
  TailorEarningsSummary,
  TailorListParams,
  TailorListResult,
  TailorPayload,
  WorkAssignment,
  WorkAssignmentCreatePayload,
  WorkAssignmentListParams,
  WorkAssignmentListResult,
  WorkAssignmentStatus,
  WorkAssignmentStatusResponse,
} from '../types/tailors';

export const tailorService = {
  async list(params: TailorListParams = {}): Promise<TailorListResult> {
    const query = new URLSearchParams();
    if (params.search) query.set('search', params.search);
    if (params.scope && params.scope !== 'active') query.set('scope', params.scope);
    if (params.page && params.page > 1) query.set('page', String(params.page));
    const qs = query.toString();
    const response = await apiClient.get<TailorListResult>(`/tailors/${qs ? `?${qs}` : ''}`);
    return response.data;
  },

  async get(id: number): Promise<Tailor> {
    const response = await apiClient.get<Tailor>(`/tailors/${id}/`);
    return response.data;
  },

  async create(payload: TailorPayload): Promise<Tailor> {
    const response = await apiClient.post<Tailor>('/tailors/', payload);
    return response.data;
  },

  async update(id: number, payload: TailorPayload): Promise<Tailor> {
    const response = await apiClient.patch<Tailor>(`/tailors/${id}/`, payload);
    return response.data;
  },

  async archive(id: number): Promise<TailorActionResponse> {
    const response = await apiClient.post<TailorActionResponse>(`/tailors/${id}/archive/`);
    return response.data;
  },

  async restore(id: number): Promise<TailorActionResponse> {
    const response = await apiClient.post<TailorActionResponse>(`/tailors/${id}/restore/`);
    return response.data;
  },

  async earnings(id: number, params: { date_from?: string; date_to?: string } = {}): Promise<TailorEarnings> {
    const query = new URLSearchParams();
    if (params.date_from) query.set('date_from', params.date_from);
    if (params.date_to) query.set('date_to', params.date_to);
    const qs = query.toString();
    const response = await apiClient.get<TailorEarnings>(`/tailors/${id}/earnings/${qs ? `?${qs}` : ''}`);
    return response.data;
  },

  async earningsSummary(): Promise<TailorEarningsSummary> {
    const response = await apiClient.get<TailorEarningsSummary>('/tailor-earnings/summary/');
    return response.data;
  },
};

export const pieceRateService = {
  async list(): Promise<PieceRateListResult> {
    const response = await apiClient.get<PieceRateListResult>('/piece-rates/');
    return response.data;
  },

  async create(payload: PieceRatePayload): Promise<PieceRate> {
    const response = await apiClient.post<PieceRate>('/piece-rates/', payload);
    return response.data;
  },

  async update(id: number, payload: Partial<PieceRatePayload>): Promise<PieceRate> {
    const response = await apiClient.patch<PieceRate>(`/piece-rates/${id}/`, payload);
    return response.data;
  },
};

export const workAssignmentService = {
  async list(params: WorkAssignmentListParams = {}): Promise<WorkAssignmentListResult> {
    const query = new URLSearchParams();
    if (params.tailor) query.set('tailor', String(params.tailor));
    if (params.order) query.set('order', String(params.order));
    if (params.garment_type) query.set('garment_type', params.garment_type);
    if (params.status) query.set('status', params.status);
    if (params.date_from) query.set('date_from', params.date_from);
    if (params.date_to) query.set('date_to', params.date_to);
    if (params.page && params.page > 1) query.set('page', String(params.page));
    const qs = query.toString();
    const response = await apiClient.get<WorkAssignmentListResult>(
      `/work-assignments/${qs ? `?${qs}` : ''}`
    );
    return response.data;
  },

  async get(id: number): Promise<WorkAssignment> {
    const response = await apiClient.get<WorkAssignment>(`/work-assignments/${id}/`);
    return response.data;
  },

  async create(payload: WorkAssignmentCreatePayload): Promise<WorkAssignment> {
    const response = await apiClient.post<WorkAssignment>('/work-assignments/', payload);
    return response.data;
  },

  async reportProgress(id: number, completedQuantity: number): Promise<WorkAssignment> {
    const response = await apiClient.patch<WorkAssignment>(`/work-assignments/${id}/`, {
      completed_quantity: completedQuantity,
    });
    return response.data;
  },

  async changeStatus(
    id: number,
    status: WorkAssignmentStatus,
    completedQuantity?: number
  ): Promise<WorkAssignmentStatusResponse> {
    const payload: Record<string, unknown> = { status };
    if (completedQuantity !== undefined) payload.completed_quantity = completedQuantity;
    const response = await apiClient.post<WorkAssignmentStatusResponse>(
      `/work-assignments/${id}/status/`,
      payload
    );
    return response.data;
  },
};
