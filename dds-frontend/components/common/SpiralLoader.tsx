'use client';
import { Box, Typography, useTheme } from '@mui/material';

// Animated spiral shown while data is being retrieved from the backend.
export default function SpiralLoader({ size = 64, label }: { size?: number; label?: string }) {
  const theme = useTheme();
  const color = theme.palette.primary.main;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 1.5, py: 8 }}>
      <svg width={size} height={size} viewBox="0 0 100 100" fill="none" aria-hidden>
        <path
          d="M50 50 m0 -4 a4 4 0 0 1 4 4 a8 8 0 0 1 -8 8 a12 12 0 0 1 12 -12 a16 16 0 0 1 -16 16 a20 20 0 0 1 20 -20 a24 24 0 0 1 -24 24 a28 28 0 0 1 28 -28 a32 32 0 0 1 -32 32 a36 36 0 0 1 36 -36 a40 40 0 0 1 -40 40"
          stroke={color}
          strokeWidth="5"
          strokeLinecap="round"
          className="spiral-path"
        />
      </svg>
      {label && <Typography variant="body2" color="text.secondary">{label}</Typography>}
      <style>{`
        .spiral-path { transform-origin: 50% 50%; animation: spiral-spin 1.8s linear infinite, spiral-pulse 1.8s ease-in-out infinite; }
        @keyframes spiral-spin { to { transform: rotate(360deg); } }
        @keyframes spiral-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
      `}</style>
    </Box>
  );
}
