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
  CircularProgress,
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { BrandMark } from '../components/ui/BrandMark';
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
        backgroundColor: '#FAF6EC',
        backgroundImage:
          'radial-gradient(1200px 600px at 50% -10%, rgba(201, 162, 39, 0.16) 0%, rgba(201, 162, 39, 0) 60%), radial-gradient(900px 500px at 100% 110%, rgba(201, 162, 39, 0.10) 0%, rgba(201, 162, 39, 0) 60%)',
        py: 4,
        px: 2,
      }}
    >
      <Container maxWidth="sm">
        <Box
          sx={{
            borderRadius: '20px',
            border: '1px solid #E7E0D0',
            overflow: 'hidden',
            backgroundColor: '#FFFFFF',
            boxShadow: '0 24px 48px -16px rgba(58, 48, 20, 0.22)',
          }}
        >
          {/* Header Branding Banner */}
          <Box
            sx={{
              background: 'linear-gradient(135deg, #8F6E10 0%, #A98216 55%, #C9A227 100%)',
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
            <BrandMark size={64} />
            <Box>
              <Typography
                variant="h4"
                sx={{ fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.02em', lineHeight: 1.2 }}
              >
                Saamu Tailors
              </Typography>
              <Typography variant="body2" sx={{ color: '#F5EBD2', mt: 0.5, fontWeight: 500 }}>
                Enterprise Tailoring Management System
              </Typography>
            </Box>
          </Box>

          <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
            {completed ? (
              <Stack spacing={2.5}>
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#242424' }}>
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
                >
                  Back to Sign In
                </Button>
              </Stack>
            ) : invalidLink ? (
              <Stack spacing={2.5}>
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#242424' }}>
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
                      color: '#A98216',
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
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#242424', mb: 1 }}>
                  Set a New Password
                </Typography>
                <Typography variant="body2" sx={{ color: '#6B6B6B', mb: 3 }}>
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
                                <LockOutlinedIcon sx={{ color: '#6B6B6B' }} />
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
                                <LockOutlinedIcon sx={{ color: '#6B6B6B' }} />
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
                          color: '#7A5E0C',
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
              backgroundColor: '#FBF6EA',
              borderTop: '1px solid #E7E0D0',
              textAlign: 'center',
            }}
          >
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              Saamu Tailors System | Single-PC Local Deployment
            </Typography>
          </Box>
        </Box>
      </Container>
    </Box>
  );
};
