import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1E3A8A', // Deep Navy Blue
      light: '#3B82F6',
      dark: '#1E293B',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#2563EB', // Royal Blue
      light: '#60A5FA',
      dark: '#1D4ED8',
      contrastText: '#FFFFFF',
    },
    success: {
      main: '#22C55E',
      light: '#4ADE80',
      dark: '#15803D',
      contrastText: '#FFFFFF',
    },
    error: {
      main: '#EF4444',
      light: '#F87171',
      dark: '#B91C1C',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#F8FAFC', // Slate background
      paper: '#FFFFFF',   // Solid surface
    },
    text: {
      primary: '#0F172A',
      secondary: '#475569',
      disabled: '#94A3B8',
    },
    divider: '#E2E8F0',
  },
  shape: {
    borderRadius: 12, // 12px border radius
  },
  typography: {
    fontFamily: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'].join(','),
    h1: {
      fontWeight: 700,
      fontSize: '2.25rem',
      letterSpacing: '-0.02em',
      color: '#0F172A',
    },
    h2: {
      fontWeight: 700,
      fontSize: '1.75rem',
      letterSpacing: '-0.01em',
      color: '#0F172A',
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.5rem',
      color: '#0F172A',
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.25rem',
      color: '#0F172A',
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.1rem',
      color: '#0F172A',
    },
    h6: {
      fontWeight: 600,
      fontSize: '1rem',
      color: '#0F172A',
    },
    subtitle1: {
      fontSize: '0.95rem',
      color: '#475569',
    },
    subtitle2: {
      fontSize: '0.85rem',
      fontWeight: 500,
      color: '#64748B',
    },
    body1: {
      fontSize: '0.95rem',
      lineHeight: 1.5,
      color: '#1E293B',
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.43,
      color: '#475569',
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
      fontSize: '0.9rem',
    },
  },
  shadows: [
    'none',
    '0 1px 2px 0 rgba(15, 23, 42, 0.05)',
    '0 1px 3px 0 rgba(15, 23, 42, 0.08), 0 1px 2px -1px rgba(15, 23, 42, 0.04)',
    '0 4px 6px -1px rgba(15, 23, 42, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.04)',
    '0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -4px rgba(15, 23, 42, 0.04)',
    '0 20px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04)',
    ...Array(19).fill('0 10px 15px -3px rgba(15, 23, 42, 0.08)'),
  ] as unknown as ReturnType<typeof createTheme>['shadows'],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          padding: '8px 16px',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 4px 6px -1px rgba(15, 23, 42, 0.1)',
          },
        },
        containedPrimary: {
          backgroundColor: '#1E3A8A',
          '&:hover': {
            backgroundColor: '#1D4ED8',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          border: '1px solid #E2E8F0',
          boxShadow: '0 1px 3px 0 rgba(15, 23, 42, 0.05)',
          backgroundImage: 'none',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          backgroundImage: 'none',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: '12px',
          },
        },
      },
    },
  },
});
