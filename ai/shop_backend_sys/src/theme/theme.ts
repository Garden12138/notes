import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    primary: {
      main: '#666FE8',
      light: '#F2F3FE',
      dark: '#545DD3',
    },
    secondary: {
      main: '#2E384D',
      light: '#8798AD',
      dark: '#5C6C8A',
    },
    success: {
      main: '#4FC051',
      light: 'rgba(75, 198, 69, 0.2)',
      dark: '#339335',
    },
    warning: {
      main: '#F1D219',
      light: 'rgba(241, 210, 25, 0.2)',
      dark: '#C7AC0A',
    },
    error: {
      main: '#FA4747',
      light: 'rgba(250, 71, 71, 0.2)',
      dark: '#D63649',
    },
    background: {
      default: '#FAFAFA',
      paper: '#FFFFFF',
    },
    grey: {
      100: '#F5F6FB',
      200: '#EFF2FF',
      300: '#BFC5D2',
      400: '#8097B1',
    },
  },
  typography: {
    fontFamily: 'Rubik, Arial, sans-serif',
    h1: {
      fontSize: '28px',
      fontWeight: 400,
      lineHeight: 1.185,
    },
    h2: {
      fontSize: '16px',
      fontWeight: 500,
      lineHeight: 1.185,
    },
    body1: {
      fontSize: '16px',
      fontWeight: 400,
      lineHeight: 1.3125,
    },
    body2: {
      fontSize: '14px',
      fontWeight: 400,
      lineHeight: 1.185,
    },
    caption: {
      fontSize: '13px',
      fontWeight: 400,
      lineHeight: 1.185,
      letterSpacing: '9.33%',
      textTransform: 'uppercase',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: '3px',
          boxShadow: '0px 5px 10px 0px rgba(46, 91, 255, 0.2)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: '5px',
            '& fieldset': {
              borderColor: '#BFC5D2',
            },
          },
        },
      },
    },
  },
}); 