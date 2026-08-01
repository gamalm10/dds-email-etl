'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  Box, Paper, Typography, TextField, Button, Alert, CircularProgress,
} from '@mui/material';
import { Lock } from '@mui/icons-material';

export default function ResetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get('email') || '';
  const [otp, setOtp] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [confirmPwd, setConfirmPwd] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState<'otp' | 'password'>('otp');
  const [resetToken, setResetToken] = useState('');
  const [success, setSuccess] = useState(false);

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch('/api/auth/verify-otp', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Invalid OTP');
      setResetToken(data.reset_token);
      setStep('password');
    } catch (err: any) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (newPwd !== confirmPwd) { setError('Passwords do not match'); return; }
    if (newPwd.length < 8) { setError('Minimum 8 characters'); return; }
    setLoading(true);
    try {
      const res = await fetch('/api/auth/reset-password', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reset_token: resetToken, new_password: newPwd }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Reset failed');
      setSuccess(true);
      setTimeout(() => router.push('/login'), 1500);
    } catch (err: any) { setError(err.message); }
    finally { setLoading(false); }
  };

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'background.default' }}>
      <Paper sx={{ p: 4, maxWidth: 400, width: '100%' }}>
        <Typography variant="h5" gutterBottom align="center">Reset Password</Typography>
        {success ? (
          <Alert severity="success">Password reset! Redirecting to login...</Alert>
        ) : step === 'otp' ? (
          <form onSubmit={handleVerifyOtp}>
            <Typography variant="body2" color="text.secondary" gutterBottom>Enter the 6-digit code sent to {email}</Typography>
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            <TextField fullWidth label="OTP Code" value={otp} onChange={(e) => setOtp(e.target.value)}
              required margin="normal" inputProps={{ maxLength: 6, pattern: '[0-9]*' }} />
            <Button type="submit" variant="contained" fullWidth disabled={loading} sx={{ mt: 2, mb: 2 }}>
              {loading ? <CircularProgress size={24} /> : 'Verify OTP'}
            </Button>
          </form>
        ) : (
          <form onSubmit={handleReset}>
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            <TextField fullWidth label="New Password" type="password" value={newPwd} onChange={(e) => setNewPwd(e.target.value)}
              required margin="normal" helperText="Minimum 8 characters"
              InputProps={{ startAdornment: <Lock sx={{ mr: 1, color: 'text.secondary' }} /> }} />
            <TextField fullWidth label="Confirm Password" type="password" value={confirmPwd} onChange={(e) => setConfirmPwd(e.target.value)}
              required margin="normal"
              InputProps={{ startAdornment: <Lock sx={{ mr: 1, color: 'text.secondary' }} /> }} />
            <Button type="submit" variant="contained" fullWidth disabled={loading} sx={{ mt: 2, mb: 2 }}>
              {loading ? <CircularProgress size={24} /> : 'Reset Password'}
            </Button>
          </form>
        )}
        <Box sx={{ textAlign: 'center' }}><Link href="/login"><Typography variant="body2" color="primary">Back to Login</Typography></Link></Box>
      </Paper>
    </Box>
  );
}
