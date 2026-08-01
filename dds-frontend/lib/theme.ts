'use client';
import { createTheme, ThemeOptions } from '@mui/material/styles';

const lightTheme: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: { main: '#1565C0', light: '#42A5F5', dark: '#0D47A1' },
    secondary: { main: '#7C4DFF', light: '#B388FF', dark: '#651FFF' },
    background: { default: '#F5F7FA', paper: '#FFFFFF' },
    success: { main: '#4CAF50' },
    warning: { main: '#FF9800' },
    error: { main: '#F44336' },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: { fontWeight: 700 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiCard: { styleOverrides: { root: { boxShadow: '0 2px 12px rgba(0,0,0,0.08)' } } },
    MuiButton: { styleOverrides: { root: { textTransform: 'none', fontWeight: 600 } } },
  },
};

const darkTheme: ThemeOptions = {
  ...lightTheme,
  palette: {
    mode: 'dark',
    primary: { main: '#42A5F5', light: '#64B5F6', dark: '#1565C0' },
    secondary: { main: '#B388FF', light: '#D1C4E9', dark: '#7C4DFF' },
    background: { default: '#0A1929', paper: '#132F4C' },
    success: { main: '#66BB6A' },
    warning: { main: '#FFA726' },
    error: { main: '#EF5350' },
  },
};

export { lightTheme, darkTheme };
