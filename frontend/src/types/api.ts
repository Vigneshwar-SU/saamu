export interface HealthStatus {
  status: string;
  application: string;
  version: string;
  database?: string;
}

export interface StandardizedApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

export const USER_ROLES = ['OWNER', 'STAFF'] as const;

export type UserRole = (typeof USER_ROLES)[number];

export interface AuthUser {
  id: number;
  username: string;
  role: UserRole;
  is_active: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: AuthUser;
}

export interface RefreshResponse {
  access: string;
}

export interface LogoutResponse {
  success: boolean;
  message?: string;
}
