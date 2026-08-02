import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  persistAccessToken,
} from './authToken';
import { normalizeApiError } from '../utils/apiErrors';
import type { RefreshResponse } from '../types/api';

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

/**
 * Called when a token refresh fails (e.g. expired/invalid refresh token).
 * The auth context registers a handler to clear state and redirect to login.
 */
let onAuthExpired: (() => void) | null = null;

export function setOnAuthExpired(handler: (() => void) | null): void {
  onAuthExpired = handler;
}

/** True for endpoints that must never trigger an automatic refresh cycle. */
function isAuthEndpoint(url?: string): boolean {
  if (!url) return false;
  return /\/auth\/(login|refresh|logout)\/?$/.test(url);
}

let isRefreshing = false;
let failedQueue: Array<(token: string | null) => void> = [];

function flushQueue(token: string | null): void {
  failedQueue.forEach((callback) => callback(token));
  failedQueue = [];
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;
  try {
    const response = await axios.post<RefreshResponse>(
      `${baseURL}/auth/refresh/`,
      { refresh: refreshToken },
      { headers: { 'Content-Type': 'application/json' }, timeout: 10000 }
    );
    persistAccessToken(response.data.access);
    return response.data.access;
  } catch {
    return null;
  }
}

apiClient.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(normalizeApiError(error))
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const axiosError = error as AxiosError;
    const original = axiosError.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    const status = axiosError.response?.status;

    const shouldAttemptRefresh =
      status === 401 &&
      original &&
      !original._retry &&
      !isAuthEndpoint(original.url);

    if (!shouldAttemptRefresh) {
      return Promise.reject(normalizeApiError(error));
    }

    original._retry = true;

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push((token) => {
          if (token) {
            original.headers = original.headers ?? {};
            original.headers.Authorization = `Bearer ${token}`;
            apiClient(original)
              .then(resolve)
              .catch((retryError) => reject(normalizeApiError(retryError)));
          } else {
            reject(normalizeApiError(error));
          }
        });
      });
    }

    isRefreshing = true;
    const newAccess = await refreshAccessToken();
    isRefreshing = false;

    if (newAccess) {
      flushQueue(newAccess);
      original.headers = original.headers ?? {};
      original.headers.Authorization = `Bearer ${newAccess}`;
      try {
        return await apiClient(original);
      } catch (retryError) {
        return Promise.reject(normalizeApiError(retryError));
      }
    }

    // Refresh failed: clear credentials and signal the auth layer.
    flushQueue(null);
    clearTokens();
    onAuthExpired?.();
    return Promise.reject(normalizeApiError(error));
  }
);
