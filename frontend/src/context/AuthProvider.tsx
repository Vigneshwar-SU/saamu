import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { authService } from '../services/authService';
import {
  clearTokens,
  getRefreshToken,
  getAccessToken,
  setTokens,
} from '../services/authToken';
import { setOnAuthExpired } from '../services/apiClient';
import { AuthContext, AuthContextValue } from './authContext';
import type { AuthUser, LoginRequest } from '../types/api';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore the session on first load: validate the stored access token via
  // /me/. The API client transparently refreshes an expired access token; if
  // that fails it clears tokens and invokes onAuthExpired below.
  useEffect(() => {
    let cancelled = false;

    async function bootstrap(): Promise<void> {
      if (!getAccessToken() || !getRefreshToken()) {
        if (!cancelled) setIsLoading(false);
        return;
      }
      try {
        const response = await authService.me();
        if (!cancelled) setUser(response.data);
      } catch {
        // Tokens are cleared by the interceptor on refresh failure.
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  // Register the unauthorized handler so any failed refresh mid-session
  // clears local auth state (redirect to login is handled by route guards).
  useEffect(() => {
    setOnAuthExpired(() => {
      setUser(null);
    });
    return () => setOnAuthExpired(null);
  }, []);

  const login = useCallback(async (credentials: LoginRequest, remember = false) => {
    const response = await authService.login(credentials);
    setTokens(response.data.access, response.data.refresh, remember);
    setUser(response.data.user);
  }, []);

  const logout = useCallback(async () => {
    const refreshToken = getRefreshToken();
    try {
      if (refreshToken) {
        await authService.logout(refreshToken);
      }
    } catch {
      // Explicit logout must still clear local credentials even if the
      // backend call fails (offline, server error, expired session).
    } finally {
      clearTokens();
      setUser(null);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: user !== null,
      isLoading,
      user,
      role: user?.role ?? null,
      login,
      logout,
    }),
    [user, isLoading, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
