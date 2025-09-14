import { createTheme, Theme } from '@mui/material/styles';

// Color system from any_agent_styles.css
const colors = {
  // Primary Colors
  primaryBlue: '#1f4788',
  primaryBlueLight: '#3f67a8',
  primaryBlueDark: '#0f2748',
  primaryGreen: '#1f7a4f',
  primaryGreenLight: '#3f9a6f',
  primaryGreenDark: '#0f5a2f',
  
  // Neutral Background System
  neutralWhite: '#ffffff',
  neutralLight: '#f8f9fa',
  neutralLighter: '#e9ecef',
  neutralMedium: '#dee2e6',
  neutralDark: '#6c757d',
  neutralDarker: '#495057',
  neutralDarkest: '#212529',
  
  // Notification Colors
  success: '#006b3c',
  successLight: '#d4edda',
  warning: '#b45309',
  warningLight: '#fff3cd',
  error: '#dc3545',
  errorLight: '#f8d7da',
  info: '#0c5aa6',
  infoLight: '#d1ecf1',
};

const anyAgentTheme: Theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: colors.primaryBlue,
      light: colors.primaryBlueLight,
      dark: colors.primaryBlueDark,
      contrastText: colors.neutralWhite,
    },
    secondary: {
      main: colors.primaryGreen,
      light: colors.primaryGreenLight,
      dark: colors.primaryGreenDark,
      contrastText: colors.neutralWhite,
    },
    error: {
      main: colors.error,
      light: colors.errorLight,
      contrastText: colors.neutralWhite,
    },
    warning: {
      main: colors.warning,
      light: colors.warningLight,
      contrastText: colors.neutralWhite,
    },
    info: {
      main: colors.info,
      light: colors.infoLight,
      contrastText: colors.neutralWhite,
    },
    success: {
      main: colors.success,
      light: colors.successLight,
      contrastText: colors.neutralWhite,
    },
    background: {
      default: colors.neutralWhite,
      paper: colors.neutralWhite,
    },
    text: {
      primary: colors.neutralDarkest,
      secondary: colors.neutralDarker,
      disabled: colors.neutralDark,
    },
    divider: colors.neutralMedium,
    action: {
      hover: colors.neutralLight,
      selected: colors.neutralLighter,
    },
  },
  typography: {
    fontFamily: '"Roboto", sans-serif',
    h1: {
      fontSize: '2rem',
      fontWeight: 500,
      color: colors.primaryBlue,
    },
    h2: {
      fontSize: '1.75rem',
      fontWeight: 500,
      color: colors.primaryBlue,
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 500,
      color: colors.primaryBlueDark,
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 500,
      color: colors.primaryBlueDark,
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 500,
      color: colors.primaryBlueDark,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
      color: colors.primaryBlueDark,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
      color: colors.neutralDarkest,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.6,
      color: colors.neutralDarker,
    },
    caption: {
      fontSize: '0.75rem',
      color: colors.neutralDark,
      fontFamily: '"Roboto Mono", monospace',
    },
  },
  spacing: 8, // 8px base spacing unit
  shape: {
    borderRadius: 4,
  },
  shadows: [
    'none',
    '0 1px 3px rgba(0, 0, 0, 0.1)',
    '0 4px 6px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
    '0 10px 15px rgba(0, 0, 0, 0.1)',
  ],
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          minHeight: '100vh',
          backgroundColor: colors.neutralWhite,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: colors.primaryBlueDark,
          color: colors.neutralWhite,
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          borderRadius: 4,
        },
        containedPrimary: {
          backgroundColor: colors.primaryBlue,
          '&:hover': {
            backgroundColor: colors.primaryBlueLight,
          },
        },
        containedSecondary: {
          backgroundColor: colors.primaryGreen,
          '&:hover': {
            backgroundColor: colors.primaryGreenLight,
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          border: `1px solid ${colors.neutralMedium}`,
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            '&.Mui-focused fieldset': {
              borderColor: colors.primaryBlue,
            },
          },
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: colors.neutralLight,
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: colors.neutralLight,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontFamily: '"Roboto Mono", monospace',
          fontSize: '0.75rem',
          fontWeight: 500,
        },
      },
    },
  },
});

export default anyAgentTheme;

// Export color constants for direct use
export { colors };