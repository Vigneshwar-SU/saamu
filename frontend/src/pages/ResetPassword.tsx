import React, { useState } from 'react';
import {
  Box,
  CardContent,
  Typography,
  TextField,
  Button,
  InputAdornment,
  IconButton,
  Link,
  Alert,
  Stack,
  Container,
  Paper,
  CircularProgress,
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import ContentCutIcon from '@mui/icons-material/ContentCut';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate, useParams } from 'react-router-dom';
import { useConfirmPasswordReset } from '../hooks/usePasswordReset';
import { normalizeApiError } from '../utils/apiErrors';

const resetPasswordSchema = z
  .object({
    newPassword: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .refine((value) => /\D/.test(value), 'Password cannot be entirely numeric'),
    confirmPassword: z.string().min(1, 'Please confirm your password'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

export const ResetPassword: React.FC = () => {
  const navigate = useNavigate();
  const { uid, token } = useParams<{ uid: string; token: string }>();
  const confirmPasswordReset = useConfirmPasswordReset();
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [resetError, setResetError] = useState<string | null>(null);
  const [invalidLink, setInvalidLink] = useState(false);
  const [completed, setCompleted] = useState(false);

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      newPassword: '',
      confirmPassword: '',
    },
  });

  const onSubmit = async (data: ResetPasswordFormData) => {
    setResetError(null);
    if (!uid || !token) {
      setInvalidLink(true);
      return;
    }
    try {
      await confirmPasswordReset.mutateAsync({
        uid,
        token,
        new_password: data.newPassword,
        confirm_password: data.confirmPassword,
      });
      setCompleted(true);
    } catch (error) {
      const apiError = normalizeApiError(error);
      if (apiError.code === 'invalid_reset_token') {
        setInvalidLink(true);
      } else {
        setResetError(apiError.message);
      }
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#F8FAFC',
        py: 4,
        px: 2,
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={2}
          sx={{
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            overflow: 'hidden',
            backgroundColor: '#FFFFFF',
          }}
        >
          {/* Header Branding Banner */}
          <Box
            sx={{
              backgroundColor: '#1E3A8A',
              color: '#FFFFFF',
              py: 4,
              px: 3,
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 1.5,
            }}
          >
            <Box
              sx={{
                width: 56,
                height: 56,
                borderRadius: '14px',
                backgroundColor: '#2563EB',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.2)',
              }}
            >
              <ContentCutIcon sx={{ fontSize: 32, color: '#FFFFFF' }} />
            </Box>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 700, color: '#FFFFFF', letterSpacing: '-0.02em' }}>
                SAAMU TAILORS
              </Typography>
              <Typography variant="body2" sx={{ color: '#93C5FD', mt: 0.5 }}>
                Tailoring Management System ERP
              </Typography>
            </Box>
          </Box>

          <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
            {completed ? (
              <Stack spacing={2.5}>
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#0F172A' }}>
                  Password Reset Successful
                </Typography>
                <Alert severity="success" sx={{ borderRadius: '10px' }}>
                  Your password has been reset successfully. You can now sign in
                  with your new password.
                </Alert>
                <Button
                  variant="contained"
                  fullWidth
                  size="large"
                  onClick={() => navigate('/login')}
                  sx={{
                    py: 1.5,
                    fontSize: '1rem',
                    fontWeight: 600,
                    backgroundColor: '#1E3A8A',
                    '&:hover': { backgroundColor: '#1D4ED8' },
                  }}
                >
                  Back to Sign In
                </Button>
              </Stack>
            ) : invalidLink ? (
              <Stack spacing={2.5}>
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#0F172A' }}>
                  Reset Link Invalid
                </Typography>
                <Alert severity="error" sx={{ borderRadius: '10px' }}>
                  This password reset link is invalid or has expired. Please
                  request a new password reset link.
                </Alert>
                <Button
                  variant="contained"
                  fullWidth
                  size="large"
                  onClick={() => navigate('/forgot-password')}
                  sx={{
                    py: 1.5,
                    fontSize: '1rem',
                    fontWeight: 600,
                    backgroundColor: '#1E3A8A',
                    '&:hover': { backgroundColor: '#1D4ED8' },
                  }}
                >
                  Request New Link
                </Button>
                <Box sx={{ textAlign: 'center' }}>
                  <Link
                    component="button"
                    type="button"
                    variant="body2"
                    onClick={() => navigate('/login')}
                    sx={{
                      color: '#2563EB',
                      fontWeight: 600,
                      textDecoration: 'none',
                      '&:hover': { textDecoration: 'underline' },
                    }}
                  >
                    Back to Sign In
                  </Link>
                </Box>
              </Stack>
            ) : (
              <>
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#0F172A', mb: 1 }}>
                  Set a New Password
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748B', mb: 3 }}>
                  Choose a strong password you have not used for this account.
                </Typography>

                {resetError && (
                  <Alert severity="error" sx={{ mb: 3, borderRadius: '10px' }}>
                    {resetError}
                  </Alert>
                )}

                <form onSubmit={handleSubmit(onSubmit)} noValidate>
                  <Stack spacing={2.5}>
                    <Controller
                      name="newPassword"
                      control={control}
                      render={({ field }) => (
                        <TextField
                          {...field}
                          label="New Password"
                          type={showNewPassword ? 'text' : 'password'}
                          fullWidth
                          variant="outlined"
                          autoComplete="new-password"
                          error={!!errors.newPassword}
                          helperText={errors.newPassword?.message}
                          InputProps={{
                            startAdornment: (
                              <InputAdornment position="start">
                                <LockOutlinedIcon sx={{ color: '#64748B' }} />
                              </InputAdornment>
                            ),
                            endAdornment: (
                              <InputAdornment position="end">
                                <IconButton
                                  aria-label="toggle password visibility"
                                  onClick={() => setShowNewPassword(!showNewPassword)}
                                  edge="end"
                                >
                                  {showNewPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                                </IconButton>
                              </InputAdornment>
                            ),
                          }}
                        />
                      )}
                    />

                    <Controller
                      name="confirmPassword"
                      control={control}
                      render={({ field }) => (
                        <TextField
                          {...field}
                          label="Confirm New Password"
                          type={showConfirmPassword ? 'text' : 'password'}
                          fullWidth
                          variant="outlined"
                          autoComplete="new-password"
                          error={!!errors.confirmPassword}
                          helperText={errors.confirmPassword?.message}
                          InputProps={{
                            startAdornment: (
                              <InputAdornment position="start">
                                <LockOutlinedIcon sx={{ color: '#64748B' }} />
                              </InputAdornment>
                            ),
                            endAdornment: (
                              <InputAdornment position="end">
                                <IconButton
                                  aria-label="toggle confirm password visibility"
                                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                  edge="end"
                                >
                                  {showConfirmPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                                </IconButton>
                              </InputAdornment>
                            ),
                          }}
                        />
                      )}
                    />

                    <Button
                      type="submit"
                      variant="contained"
                      fullWidth
                      size="large"
                      disabled={confirmPasswordReset.isPending}
                      startIcon={
                        confirmPasswordReset.isPending ? (
                          <CircularProgress size={18} color="inherit" />
                        ) : undefined
                      }
                      sx={{
                        py: 1.5,
                        fontSize: '1rem',
                        fontWeight: 600,
                        backgroundColor: '#1E3A8A',
                        '&:hover': { backgroundColor: '#1D4ED8' },
                      }}
                    >
                      {confirmPasswordReset.isPending ? 'Resetting Password...' : 'Reset Password'}
                    </Button>

                    <Box sx={{ textAlign: 'center' }}>
                      <Link
                        component="button"
                        type="button"
                        variant="body2"
                        onClick={() => navigate('/login')}
                        sx={{
                          color: '#2563EB',
                          fontWeight: 600,
                          textDecoration: 'none',
                          '&:hover': { textDecoration: 'underline' },
                        }}
                      >
                        Back to Sign In
                      </Link>
                    </Box>
                  </Stack>
                </form>
              </>
            )}
          </CardContent>

          <Box
            sx={{
              py: 2,
              px: 3,
              backgroundColor: '#F1F5F9',
              borderTop: '1px solid #E2E8F0',
              textAlign: 'center',
            }}
          >
            <Typography variant="caption" sx={{ color: '#64748B' }}>
              Saamu Tailors System Foundation Sprint | Single-PC Local Deployment
            </Typography>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};
