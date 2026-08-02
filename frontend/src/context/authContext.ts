import { createContext } from 'react';
import type { AuthUser, LoginRequest, UserRole } from '../types/api';

export interface AuthContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: AuthUser | null;
  role: UserRole | null;
  login: (credentials: LoginRequest, remember?: boolean) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);
