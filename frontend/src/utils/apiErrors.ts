import { AxiosError } from 'axios';
import type { StandardizedApiError } from '../types/api';

export class ApiError extends Error {
  readonly status?: number;
  readonly code: string;
  readonly details?: unknown;

  constructor(message: string, status?: number, code = 'unknown_error', details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function normalizeApiError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    return error;
  }

  if (error && typeof error === 'object' && 'isAxiosError' in error) {
    const axiosError = error as AxiosError<StandardizedApiError>;
    const body = axiosError.response?.data;

    if (body && body.error && typeof body.error.message === 'string') {
      return new ApiError(body.error.message, axiosError.response?.status, body.error.code, body.error.details);
    }

    if (axiosError.response) {
      return new ApiError(
        axiosError.response.statusText || 'Request failed.',
        axiosError.response.status,
        'request_failed'
      );
    }

    if (axiosError.code === 'ECONNABORTED') {
      return new ApiError(
        'The server took too long to respond. Please try again.',
        undefined,
        'timeout',
      );
    }

    if (axiosError.code === 'ERR_NETWORK') {
      return new ApiError(
        'Unable to reach the server. Please check that the backend is running.',
        undefined,
        'network_error',
      );
    }

    return new ApiError('A network error occurred. Please check your connection.', undefined, 'network_error');
  }

  if (error instanceof Error) {
    return new ApiError(error.message, undefined, 'unknown_error');
  }

  return new ApiError('An unexpected error occurred.', undefined, 'unknown_error');
}

export function getApiErrorMessage(error: unknown): string {
  return normalizeApiError(error).message;
}
