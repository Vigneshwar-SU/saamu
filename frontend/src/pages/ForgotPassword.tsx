import React, { useState } from 'react';
import {
  Box,
  CardContent,
  Typography,
  TextField,
  Button,
  FormControl,
  FormHelperText,
  InputAdornment,
  InputLabel,
  Link,
  Alert,
  MenuItem,
  Select,
  Stack,
  Container,
  Paper,
  CircularProgress,
} from '@mui/material';
import ContentCutIcon from '@mui/icons-material/ContentCut';
import MailOutlineIcon from '@mui/icons-material/MailOutline';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { useRequestPasswordReset } from '../hooks/usePasswordReset';
import { getApiErrorMessage } from '../utils/apiErrors';
import { USER_ROLES, type UserRole } from '../types/api';

const forgotPasswordSchema = z.object({
  accountType: z.enum(USER_ROLES, {
    required_error: 'Please select an account type',
  }),
  email: z.string().email('Enter a valid email address'),
});

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

export const ForgotPassword: React.FC = () => {
  const navigate = useNavigate();
  const requestPasswordReset = useRequestPasswordReset();
  const [resetError, setResetError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      accountType: 'OWNER',
      email: '',
    },
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setResetError(null);
    try {
      await requestPasswordReset.mutateAsync(data.email.trim());
      setSubmitted(true);
    } catch (error) {
      setResetError(getApiErrorMessage(error));
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
            {submitted ? (
              <Stack spacing={2.5}>
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#0F172A' }}>
                  Check Your Inbox
                </Typography>
                <Alert severity="success" sx={{ borderRadius: '10px' }}>
                  If an account exists with this email address, a password reset
                  link has been sent. Please check your inbox (and spam folder)
                  and follow the link. The link is valid for 15 minutes.
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
            ) : (
              <>
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#0F172A', mb: 1 }}>
                  Reset Your Password
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748B', mb: 3 }}>
                  Enter the email address linked to your account and we will send
                  you a password reset link.
                </Typography>

                {resetError && (
                  <Alert severity="error" sx={{ mb: 3, borderRadius: '10px' }}>
                    {resetError}
                  </Alert>
                )}

                <form onSubmit={handleSubmit(onSubmit)} noValidate>
                  <Stack spacing={2.5}>
                    <Controller
                      name="accountType"
                      control={control}
                      render={({ field }) => (
                        <FormControl fullWidth variant="outlined" error={!!errors.accountType}>
                          <InputLabel>Account Type</InputLabel>
                          <Select
                            {...field}
                            label="Account Type"
                            value={field.value}
                            onChange={(event) => field.onChange(event.target.value as UserRole)}
                          >
                            <MenuItem value="OWNER">Owner</MenuItem>
                            <MenuItem value="STAFF">Staff</MenuItem>
                          </Select>
                          {errors.accountType && (
                            <FormHelperText>{errors.accountType.message}</FormHelperText>
                          )}
                        </FormControl>
                      )}
                    />

                    <Controller
                      name="email"
                      control={control}
                      render={({ field }) => (
                        <TextField
                          {...field}
                          label="Email Address"
                          type="email"
                          fullWidth
                          variant="outlined"
                          autoComplete="email"
                          error={!!errors.email}
                          helperText={errors.email?.message}
                          InputProps={{
                            startAdornment: (
                              <InputAdornment position="start">
                                <MailOutlineIcon sx={{ color: '#64748B' }} />
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
                      disabled={requestPasswordReset.isPending}
                      startIcon={
                        requestPasswordReset.isPending ? (
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
                      {requestPasswordReset.isPending ? 'Sending...' : 'Send Reset Link'}
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
