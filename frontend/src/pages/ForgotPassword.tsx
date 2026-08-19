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
  CircularProgress,
} from '@mui/material';
import MailOutlineIcon from '@mui/icons-material/MailOutline';
import { BrandMark } from '../components/ui/BrandMark';
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
                sx={{
                  fontWeight: 800,
                  color: '#FFFFFF',
                  letterSpacing: '-0.02em',
                  lineHeight: 1.2,
                }}
              >
                Saamu Tailors
              </Typography>
              <Typography variant="body2" sx={{ color: '#F5EBD2', mt: 0.5, fontWeight: 500 }}>
                Enterprise Tailoring Management System
              </Typography>
            </Box>
          </Box>

          <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
            {submitted ? (
              <Stack spacing={2.5}>
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#242424' }}>
                  Check Your Inbox
                </Typography>
                <Alert severity="success" sx={{ borderRadius: '10px' }}>
                  If an account exists with this email address, a password reset link has been sent.
                  Please check your inbox (and spam folder) and follow the link. The link is valid
                  for 15 minutes.
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
            ) : (
              <>
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#242424', mb: 1 }}>
                  Reset Your Password
                </Typography>
                <Typography variant="body2" sx={{ color: '#6B6B6B', mb: 3 }}>
                  Enter the email address linked to your account and we will send you a password
                  reset link.
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
                                <MailOutlineIcon sx={{ color: '#6B6B6B' }} />
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
              Saamu Tailors Enterprise Management System
            </Typography>
          </Box>
        </Box>
      </Container>
    </Box>
  );
};
