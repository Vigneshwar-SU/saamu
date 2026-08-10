import { useMutation } from '@tanstack/react-query';
import { authService } from '../services/authService';
import type { PasswordResetConfirmPayload } from '../types/api';

export const useRequestPasswordReset = () => {
  return useMutation({
    mutationFn: (email: string) => authService.requestPasswordReset(email),
  });
};

export const useConfirmPasswordReset = () => {
  return useMutation({
    mutationFn: (payload: PasswordResetConfirmPayload) =>
      authService.confirmPasswordReset(payload),
  });
};
