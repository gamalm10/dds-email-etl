'use client';
import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Box, Card, CardContent, TextField, Button, Typography, Alert, InputAdornment, IconButton,
} from '@mui/material';
import { Email, Lock, Visibility, VisibilityOff, DarkModeRounded } from '@mui/icons-material';
import { useAuthStore } from '@/stores/authStore';
import api from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPwd, setShowPwd] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const searchParams = useSearchParams();
  const sessionExpired = searchParams.get('expired') === 'true';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await api.post('auth/login', { email, password });
      login(res.data.user, res.data.access_token, res.data.refresh_token);
      router.push('/');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'background.default' }}>
      <Card sx={{ maxWidth: 440, width: '100%', mx: 2 }}>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <DarkModeRounded sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
            <Typography variant="h5" fontWeight={700}>DDS Email ETL</Typography>
            <Typography variant="body2" color="text.secondary">Supply Chain Intelligence Platform</Typography>
          </Box>
          {sessionExpired && <Alert severity="warning" sx={{ mb: 2 }}>Your session has expired. Please login again.</Alert>}
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <Box component="form" onSubmit={handleSubmit}>
            <TextField fullWidth label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              margin="normal" required InputProps={{ startAdornment: <InputAdornment position="start"><Email /></InputAdornment> }} />
            <TextField fullWidth label="Password" type={showPwd ? 'text' : 'password'} value={password}
              onChange={(e) => setPassword(e.target.value)} margin="normal" required
              InputProps={{ startAdornment: <InputAdornment position="start"><Lock /></InputAdornment>,
                endAdornment: <InputAdornment position="end"><IconButton onClick={() => setShowPwd(!showPwd)} edge="end">{showPwd ? <VisibilityOff /> : <Visibility />}</IconButton></InputAdornment> }} />
             <Button type="submit" fullWidth variant="contained" size="large" disabled={loading}
              sx={{ mt: 3, py: 1.5 }}>
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
            <Box sx={{ textAlign: 'right', mt: 1 }}>
              <Typography component="a" href="/forgot-password" color="primary" variant="body2" sx={{ cursor: 'pointer' }}>Forgot password?</Typography>
            </Box>
          </Box>
          <Typography variant="body2" align="center" sx={{ mt: 2 }}>
            Don&apos;t have an account?{' '}
            <Typography component="a" href="/register" color="primary" sx={{ cursor: 'pointer', fontWeight: 600 }}>Register</Typography>
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
