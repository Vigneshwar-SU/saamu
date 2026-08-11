import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  FormControl,
  FormControlLabel,
  FormHelperText,
  Checkbox,
  InputLabel,
  InputAdornment,
  IconButton,
  MenuItem,
  Link,
  Alert,
  Select,
  Stack,
  Container,
  CardContent,
  CircularProgress,
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import PersonOutlineIcon from '@mui/icons-material/PersonOutline';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { getApiErrorMessage } from '../utils/apiErrors';
import { USER_ROLES, type UserRole } from '../types/api';
import { BrandMark } from '../components/ui/BrandMark';

// Zod Validation Schema
const loginSchema = z.object({
  accountType: z.enum(USER_ROLES, {
    required_error: 'Please select an account type',
  }),
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
      accountType: 'OWNER',
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
        Boolean(data.rememberMe),
        data.accountType
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
            <Typography variant="h5" sx={{ fontWeight: 700, color: '#242424', mb: 1 }}>
              Sign in to your account
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3 }}>
              Enter your credentials to access the tailoring operations dashboard.
            </Typography>

            {loginError && (
              <Alert severity="error" sx={{ mb: 3, borderRadius: '10px' }}>
                {loginError}
              </Alert>
            )}

            <form onSubmit={handleSubmit(onSubmit)} noValidate>
              <Stack spacing={2.5}>
                {/* Account Type Input */}
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
                            <PersonOutlineIcon sx={{ color: 'text.secondary' }} />
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
                            <LockOutlinedIcon sx={{ color: 'text.secondary' }} />
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
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
                  <Controller
                    name="rememberMe"
                    control={control}
                    render={({ field }) => (
                      <FormControlLabel
                        control={<Checkbox {...field} checked={field.value} color="primary" />}
                        label={<Typography variant="body2" sx={{ color: 'text.secondary' }}>Remember Me</Typography>}
                      />
                    )}
                  />

                  <Link
                    component="button"
                    type="button"
                    variant="body2"
                    onClick={(e) => {
                      e.preventDefault();
                      navigate('/forgot-password');
                    }}
                    sx={{
                      color: '#7A5E0C',
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

export default Login;
