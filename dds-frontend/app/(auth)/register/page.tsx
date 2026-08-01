'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Card, CardContent, TextField, Button, Typography, Alert } from '@mui/material';
import api from '@/lib/api';

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ username: '', email: '', password: '', confirm: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password !== form.confirm) { setError('Passwords do not match'); return; }
    setLoading(true);
    setError('');
    try {
      await api.post('auth/register', { username: form.username, email: form.email, password: form.password });
      setSuccess('Account created! Redirecting...');
      setTimeout(() => router.push('/login'), 1500);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'background.default' }}>
      <Card sx={{ maxWidth: 440, width: '100%', mx: 2 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h5" fontWeight={700} textAlign="center" mb={3}>Create Account</Typography>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
          <Box component="form" onSubmit={handleSubmit}>
            <TextField fullWidth label="Username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} margin="normal" required />
            <TextField fullWidth label="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} margin="normal" required />
            <TextField fullWidth label="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} margin="normal" required />
            <TextField fullWidth label="Confirm Password" type="password" value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} margin="normal" required />
            <Button type="submit" fullWidth variant="contained" size="large" disabled={loading} sx={{ mt: 3, py: 1.5 }}>
              {loading ? 'Creating...' : 'Register'}
            </Button>
          </Box>
          <Typography variant="body2" align="center" sx={{ mt: 2 }}>
            Already have an account? <Typography component="a" href="/login" color="primary" sx={{ cursor: 'pointer', fontWeight: 600 }}>Sign In</Typography>
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
