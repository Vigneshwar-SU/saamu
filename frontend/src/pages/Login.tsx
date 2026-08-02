import React, { useEffect, useState } from 'react';
import {
  Box,
  CardContent,
  Typography,
  TextField,
  Button,
  FormControlLabel,
  Checkbox,
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
import PersonOutlineIcon from '@mui/icons-material/PersonOutline';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { getApiErrorMessage } from '../utils/apiErrors';

// Zod Validation Schema
const loginSchema = z.object({
  username: z.string().min(1, 'Username or Email is required'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  rememberMe: z.boolean().optional(),
});

type LoginFormData = z.infer<typeof loginSchema>;

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
      rememberMe: false,
    },
  });

  // Already authenticated (e.g. visited /login directly) -> ERP dashboard.
  useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as { from?: string } | null)?.from;
      navigate(from && from !== '/login' ? from : '/dashboard', { replace: true });
    }
  }, [isAuthenticated, location.state, navigate]);

  const onSubmit = async (data: LoginFormData) => {
    setLoginError(null);
    try {
      await login(
        { username: data.username.trim(), password: data.password },
        Boolean(data.rememberMe)
      );
      // Redirect happens via the isAuthenticated effect above.
    } catch (error) {
      setLoginError(getApiErrorMessage(error));
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
            <Typography variant="h5" sx={{ fontWeight: 700, color: '#0F172A', mb: 1 }}>
              Sign In to Your Account
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B', mb: 3 }}>
              Enter your credentials to access the tailoring operations dashboard.
            </Typography>

            {loginError && (
              <Alert severity="error" sx={{ mb: 3, borderRadius: '10px' }}>
                {loginError}
              </Alert>
            )}

            <form onSubmit={handleSubmit(onSubmit)} noValidate>
              <Stack spacing={2.5}>
                {/* Username Input */}
                <Controller
                  name="username"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Username or Email"
                      fullWidth
                      variant="outlined"
                      autoComplete="username"
                      error={!!errors.username}
                      helperText={errors.username?.message}
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <PersonOutlineIcon sx={{ color: '#64748B' }} />
                          </InputAdornment>
                        ),
                      }}
                    />
                  )}
                />

                {/* Password Input */}
                <Controller
                  name="password"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Password"
                      type={showPassword ? 'text' : 'password'}
                      fullWidth
                      variant="outlined"
                      autoComplete="current-password"
                      error={!!errors.password}
                      helperText={errors.password?.message}
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
                              onClick={() => setShowPassword(!showPassword)}
                              edge="end"
                            >
                              {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                    />
                  )}
                />

                {/* Remember Me & Forgot Password */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Controller
                    name="rememberMe"
                    control={control}
                    render={({ field }) => (
                      <FormControlLabel
                        control={<Checkbox {...field} checked={field.value} color="primary" />}
                        label={<Typography variant="body2" sx={{ color: '#475569' }}>Remember Me</Typography>}
                      />
                    )}
                  />

                  <Link
                    component="button"
                    type="button"
                    variant="body2"
                    onClick={(e) => {
                      e.preventDefault();
                      alert('Password reset functionality placeholder');
                    }}
                    sx={{
                      color: '#2563EB',
                      fontWeight: 600,
                      textDecoration: 'none',
                      '&:hover': { textDecoration: 'underline' },
                    }}
                  >
                    Forgot Password?
                  </Link>
                </Box>

                {/* Login Button */}
                <Button
                  type="submit"
                  variant="contained"
                  fullWidth
                  size="large"
                  disabled={isSubmitting}
                  startIcon={isSubmitting ? <CircularProgress size={18} color="inherit" /> : undefined}
                  sx={{
                    py: 1.5,
                    fontSize: '1rem',
                    fontWeight: 600,
                    backgroundColor: '#1E3A8A',
                    '&:hover': {
                      backgroundColor: '#1D4ED8',
                    },
                  }}
                >
                  {isSubmitting ? 'Signing In...' : 'Sign In'}
                </Button>
              </Stack>
            </form>
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
