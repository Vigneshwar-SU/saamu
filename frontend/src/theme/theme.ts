import { createTheme } from '@mui/material/styles';

// ---------------------------------------------------------------------------
// Saamu Tailors — "Gold & White" design system
// ---------------------------------------------------------------------------
// Gold is used sparingly as an accent. Deep gold (#8F6E10) powers interactive
// elements so that text on it stays readable (WCAG AA ~4.9:1 on white labels).
// Warm off-white surfaces replace the old navy/slate look.
// ---------------------------------------------------------------------------

declare module '@mui/material/styles' {
  interface Palette {
    gold: {
      main: string;
      dark: string;
      deep: string;
      light: string;
      faint: string;
    };
  }
  interface PaletteOptions {
    gold?: {
      main?: string;
      dark?: string;
      deep?: string;
      light?: string;
      faint?: string;
    };
  }
}

const palette = {
  mode: 'light' as const,
  primary: {
    main: '#8F6E10', // Deep gold — accessible with white text
    dark: '#7A5E0C',
    light: '#A98216',
    contrastText: '#FFFFFF',
  },
  secondary: {
    main: '#6B5E44', // Warm taupe-brown
    dark: '#544A35',
    light: '#8A7A5C',
    contrastText: '#FFFFFF',
  },
  gold: {
    main: '#C9A227',
    dark: '#A98216',
    deep: '#8F6E10',
    light: '#E8D79A',
    faint: '#F5EBD2',
  },
  success: {
    main: '#2E7D52',
    light: '#4C9A6C',
    dark: '#1F5C3C',
    contrastText: '#FFFFFF',
  },
  warning: {
    main: '#B25E00',
    light: '#C97A2E',
    dark: '#8F4A00',
    contrastText: '#FFFFFF',
  },
  error: {
    main: '#B3402F',
    light: '#C95D4B',
    dark: '#8F2F22',
    contrastText: '#FFFFFF',
  },
  info: {
    main: '#6B5E44',
    light: '#8A7A5C',
    dark: '#544A35',
    contrastText: '#FFFFFF',
  },
  background: {
    default: '#FAF6EC', // Warm off-white canvas
    paper: '#FFFFFF',
  },
  text: {
    primary: '#242424',
    secondary: '#6B6B6B',
    disabled: '#A29B8E',
  },
  divider: '#E7E0D0',
};

const typography = {
  fontFamily: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'].join(','),
  h1: {
    fontWeight: 700,
    fontSize: '2rem',
    letterSpacing: '-0.02em',
    color: palette.text.primary,
  },
  h2: {
    fontWeight: 700,
    fontSize: '1.625rem',
    letterSpacing: '-0.01em',
    color: palette.text.primary,
  },
  h3: {
    fontWeight: 600,
    fontSize: '1.375rem',
    color: palette.text.primary,
  },
  h4: {
    fontWeight: 600,
    fontSize: '1.25rem',
    color: palette.text.primary,
  },
  h5: {
    fontWeight: 600,
    fontSize: '1.125rem',
    color: palette.text.primary,
  },
  h6: {
    fontWeight: 600,
    fontSize: '1rem',
    color: palette.text.primary,
  },
  subtitle1: {
    fontSize: '1rem',
    color: palette.text.secondary,
  },
  subtitle2: {
    fontSize: '0.875rem',
    fontWeight: 500,
    color: palette.text.secondary,
  },
  body1: {
    fontSize: '1rem',
    lineHeight: 1.55,
    color: palette.text.primary,
  },
  body2: {
    fontSize: '0.875rem',
    lineHeight: 1.5,
    color: palette.text.secondary,
  },
  button: {
    textTransform: 'none',
    fontWeight: 600,
    fontSize: '0.9375rem',
    letterSpacing: '0.01em',
  },
};

const shadows = [
  'none',
  '0 1px 2px 0 rgba(58, 48, 20, 0.05)',
  '0 1px 3px 0 rgba(58, 48, 20, 0.07), 0 1px 2px -1px rgba(58, 48, 20, 0.05)',
  '0 4px 8px -1px rgba(58, 48, 20, 0.08), 0 2px 4px -2px rgba(58, 48, 20, 0.05)',
  '0 10px 16px -3px rgba(58, 48, 20, 0.08), 0 4px 6px -4px rgba(58, 48, 20, 0.04)',
  '0 20px 28px -5px rgba(58, 48, 20, 0.09), 0 8px 10px -6px rgba(58, 48, 20, 0.04)',
  ...Array(19).fill('0 10px 15px -3px rgba(58, 48, 20, 0.08)'),
] as unknown as ReturnType<typeof createTheme>['shadows'];

const components: NonNullable<ReturnType<typeof createTheme>['components']> = {
  MuiButtonBase: {
    styleOverrides: {
      root: {
        '&:focus-visible': {
          outline: `2px solid ${palette.gold.main}`,
          outlineOffset: 2,
        },
      },
    },
  },
  MuiButton: {
    styleOverrides: {
      root: {
        borderRadius: 10,
        padding: '8px 18px',
        boxShadow: 'none',
        minHeight: 40,
        '&:hover': {
          boxShadow: '0 4px 8px -1px rgba(58, 48, 20, 0.14)',
        },
        '&:active': {
          boxShadow: 'none',
        },
      },
      sizeMedium: {
        minHeight: 44,
      },
      sizeLarge: {
        minHeight: 52,
        padding: '12px 26px',
        fontSize: '1rem',
      },
      containedPrimary: {
        backgroundColor: palette.primary.main,
        '&:hover': {
          backgroundColor: palette.primary.dark,
        },
      },
      outlinedPrimary: {
        borderColor: '#CBB98A',
        color: palette.primary.dark,
        '&:hover': {
          borderColor: palette.gold.dark,
          backgroundColor: palette.gold.faint,
        },
      },
      textPrimary: {
        color: palette.primary.dark,
        '&:hover': {
          backgroundColor: palette.gold.faint,
        },
      },
      contained: {
        '&.Mui-disabled': {
          backgroundColor: '#EDE8DB',
          color: '#A29B8E',
        },
      },
    },
  },
  MuiIconButton: {
    styleOverrides: {
      root: {
        color: '#5A5448',
        borderRadius: 10,
      },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: {
        borderRadius: 14,
        border: `1px solid ${palette.divider}`,
        boxShadow: '0 1px 3px 0 rgba(58, 48, 20, 0.05)',
        backgroundImage: 'none',
      },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: {
        borderRadius: 12,
        backgroundImage: 'none',
      },
      elevation1: {
        boxShadow: '0 1px 3px 0 rgba(58, 48, 20, 0.06)',
      },
    },
  },
  MuiTextField: {
    styleOverrides: {
      root: {
        '& .MuiOutlinedInput-root': {
          borderRadius: 10,
        },
      },
    },
  },
  MuiOutlinedInput: {
    styleOverrides: {
      root: {
        borderRadius: 10,
        backgroundColor: '#FFFFFF',
        '& .MuiOutlinedInput-notchedOutline': {
          borderColor: '#D9D2C2',
        },
        '&:hover .MuiOutlinedInput-notchedOutline': {
          borderColor: palette.gold.dark,
        },
        '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
          borderColor: palette.primary.main,
          borderWidth: 2,
        },
        '&.Mui-error .MuiOutlinedInput-notchedOutline': {
          borderColor: palette.error.main,
        },
      },
    },
  },
  MuiInputLabel: {
    styleOverrides: {
      root: {
        '&.Mui-focused': {
          color: palette.primary.dark,
        },
      },
    },
  },
  MuiSelect: {
    styleOverrides: {
      select: {
        '&:focus': {
          backgroundColor: 'transparent',
        },
      },
    },
  },
  MuiTableContainer: {
    styleOverrides: {
      root: {
        borderRadius: 12,
        border: `1px solid ${palette.divider}`,
      },
    },
  },
  MuiTableCell: {
    styleOverrides: {
      root: {
        borderBottom: `1px solid ${palette.divider}`,
      },
      head: {
        backgroundColor: '#FBF6EA',
        color: palette.text.secondary,
        fontWeight: 700,
        fontSize: '0.8125rem',
        letterSpacing: '0.02em',
        textTransform: 'none',
      },
      body: {
        color: palette.text.primary,
        fontSize: '0.9375rem',
        paddingTop: 14,
        paddingBottom: 14,
      },
    },
  },
  MuiTableRow: {
    styleOverrides: {
      root: {
        '&:hover': {
          backgroundColor: '#FCF8EF',
        },
        '&:last-of-type .MuiTableCell-body': {
          borderBottom: 'none',
        },
      },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        fontWeight: 600,
      },
    },
  },
  MuiDialog: {
    styleOverrides: {
      paper: {
        borderRadius: 16,
        boxShadow: '0 24px 48px -12px rgba(58, 48, 20, 0.25)',
      },
    },
  },
  MuiDialogTitle: {
    styleOverrides: {
      root: {
        fontWeight: 700,
        fontSize: '1.125rem',
        paddingTop: 24,
        paddingBottom: 16,
      },
    },
  },
  MuiDialogActions: {
    styleOverrides: {
      root: {
        padding: '16px 24px',
      },
    },
  },
  MuiDialogContent: {
    styleOverrides: {
      root: {
        paddingTop: 8,
      },
    },
  },
  MuiTabs: {
    styleOverrides: {
      root: {
        '& .MuiTabs-indicator': {
          backgroundColor: palette.primary.dark,
          height: 3,
          borderRadius: 3,
        },
      },
    },
  },
  MuiTab: {
    styleOverrides: {
      root: {
        textTransform: 'none',
        fontWeight: 600,
        color: palette.text.secondary,
        '&.Mui-selected': {
          color: palette.primary.dark,
        },
      },
    },
  },
  MuiPaginationItem: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        '&.Mui-selected': {
          backgroundColor: palette.primary.main,
          color: '#FFFFFF',
          '&:hover': {
            backgroundColor: palette.primary.dark,
          },
        },
      },
    },
  },
  MuiAlert: {
    styleOverrides: {
      root: {
        borderRadius: 10,
      },
    },
  },
  MuiLinearProgress: {
    styleOverrides: {
      root: {
        height: 8,
        borderRadius: 4,
        backgroundColor: palette.gold.faint,
      },
      bar: {
        borderRadius: 4,
      },
    },
  },
  MuiTooltip: {
    styleOverrides: {
      tooltip: {
        backgroundColor: '#2E2A22',
        fontSize: '0.8125rem',
      },
    },
  },
  MuiDivider: {
    styleOverrides: {
      root: {
        borderColor: palette.divider,
      },
    },
  },
  MuiAppBar: {
    styleOverrides: {
      root: {
        backgroundColor: '#FFFFFF',
        color: palette.text.primary,
      },
    },
  },
  MuiList: {
    styleOverrides: {
      root: {
        paddingTop: 4,
        paddingBottom: 4,
      },
    },
  },
  MuiMenuItem: {
    styleOverrides: {
      root: {
        '&.Mui-selected': {
          backgroundColor: palette.gold.faint,
          color: palette.primary.dark,
          '&:hover': {
            backgroundColor: palette.gold.light,
          },
        },
      },
    },
  },
  MuiLink: {
    styleOverrides: {
      root: {
        color: palette.primary.dark,
      },
    },
  },
  MuiBreadcrumbs: {
    styleOverrides: {
      root: {
        '& a': {
          color: palette.text.secondary,
          textDecoration: 'none',
          '&:hover': {
            color: palette.primary.dark,
          },
        },
      },
      separator: {
        color: '#B5AC98',
      },
    },
  },
  MuiSkeleton: {
    styleOverrides: {
      root: {
        backgroundColor: '#EDE7D9',
      },
    },
  },
  MuiCircularProgress: {
    styleOverrides: {
      root: {
        color: palette.primary.main,
      },
    },
  },
  MuiAvatar: {
    styleOverrides: {
      root: {
        backgroundColor: palette.gold.dark,
        color: '#FFFFFF',
      },
    },
  },
  MuiBackdrop: {
    styleOverrides: {
      root: {
        backgroundColor: 'rgba(36, 28, 10, 0.4)',
      },
    },
  },
  MuiFormHelperText: {
    styleOverrides: {
      root: {
        '&.Mui-error': {
          color: palette.error.main,
        },
      },
    },
  },
};

export const theme = createTheme({
  palette,
  shape: {
    borderRadius: 12,
  },
  typography,
  shadows,
  components,
});
