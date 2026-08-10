import { apiClient } from './apiClient';
import type {
  AuthUser,
  LoginRequest,
  LoginResponse,
  LogoutResponse,
  MessageResponse,
  PasswordResetConfirmPayload,
  RefreshResponse,
} from '../types/api';

export const authService = {
  login(credentials: LoginRequest) {
    return apiClient.post<LoginResponse>('/auth/login/', credentials);
  },

  refresh(refreshToken: string) {
    return apiClient.post<RefreshResponse>('/auth/refresh/', { refresh: refreshToken });
  },

  me() {
    return apiClient.get<AuthUser>('/auth/me/');
  },

  logout(refreshToken: string) {
    return apiClient.post<LogoutResponse>('/auth/logout/', { refresh: refreshToken });
  },

  requestPasswordReset(email: string) {
    return apiClient.post<MessageResponse>('/auth/password-reset/', { email });
  },

  confirmPasswordReset(payload: PasswordResetConfirmPayload) {
    return apiClient.post<MessageResponse>('/auth/password-reset/confirm/', payload);
  },
};
