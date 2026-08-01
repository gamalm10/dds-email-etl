'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Box, Paper, Typography, TextField, Button, Alert, CircularProgress,
} from '@mui/material';
import { Email } from '@mui/icons-material';

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to send OTP');
      setSuccess(true);
      setTimeout(() => router.push(`/reset-password?email=${encodeURIComponent(email)}`), 2000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'background.default' }}>
      <Paper sx={{ p: 4, maxWidth: 400, width: '100%' }}>
        <Typography variant="h5" gutterBottom align="center">Forgot Password</Typography>
        {success ? (
          <Alert severity="success">OTP sent to {email}. Redirecting...</Alert>
        ) : (
          <form onSubmit={handleSubmit}>
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            <TextField fullWidth label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              required margin="normal" InputProps={{ startAdornment: <Email sx={{ mr: 1, color: 'text.secondary' }} /> }} />
            <Button type="submit" variant="contained" fullWidth disabled={loading} sx={{ mt: 2, mb: 2 }}>
              {loading ? <CircularProgress size={24} /> : 'Send OTP'}
            </Button>
            <Box sx={{ textAlign: 'center' }}><Link href="/login"><Typography variant="body2" color="primary">Back to Login</Typography></Link></Box>
          </form>
        )}
      </Paper>
    </Box>
  );
}
