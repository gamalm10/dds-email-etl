'use client';
import { useEffect, useState } from 'react';
import {
  Box, Card, CardContent, Typography, Button, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Select, MenuItem, FormControl, InputLabel, Chip, IconButton, Alert, Switch, FormControlLabel,
} from '@mui/material';
import { Add, Edit, Delete, Refresh } from '@mui/icons-material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import api from '@/lib/api';

interface User {
  id: number; username: string; email: string; role_name: string; is_active: boolean; last_login: string;
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialog, setDialog] = useState(false);
  const [editUser, setEditUser] = useState<Partial<User> & { password?: string }>({});
  const [error, setError] = useState('');

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await api.get('v1/users');
      setUsers(res.data);
    } catch { setError('Failed to load users'); } finally { setLoading(false); }
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleSave = async () => {
    try {
      if (editUser.id) {
        await api.put(`v1/users/${editUser.id}`, editUser);
      } else {
        await api.post('auth/register', editUser);
      }
      setDialog(false);
      fetchUsers();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Save failed');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this user?')) return;
    try {
      await api.delete(`v1/users/${id}`);
      fetchUsers();
    } catch { setError('Delete failed'); }
  };

  const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'username', headerName: 'Username', flex: 1 },
    { field: 'email', headerName: 'Email', flex: 1 },
    { field: 'role_name', headerName: 'Role', width: 100, renderCell: (p) => <Chip label={p.value} size="small" color={p.value === 'admin' ? 'error' : p.value === 'manager' ? 'warning' : 'default'} /> },
    { field: 'is_active', headerName: 'Active', width: 80, type: 'boolean' },
    { field: 'last_login', headerName: 'Last Login', width: 160, valueFormatter: (p) => p ? new Date(p).toLocaleString() : '-' },
    {
      field: 'actions', headerName: '', width: 100, sortable: false,
      renderCell: (p) => (
        <Box>
          <IconButton size="small" onClick={() => { setEditUser(p.row); setDialog(true); }}><Edit fontSize="small" /></IconButton>
          <IconButton size="small" onClick={() => handleDelete(p.row.id)}><Delete fontSize="small" /></IconButton>
        </Box>
      ),
    },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Users</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton onClick={fetchUsers}><Refresh /></IconButton>
          <Button variant="contained" startIcon={<Add />} onClick={() => { setEditUser({ role_name: 'viewer', is_active: true }); setDialog(true); }}>Add User</Button>
        </Box>
      </Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Card>
        <DataGrid rows={users} columns={columns} loading={loading} autoHeight
          pageSizeOptions={[10, 25, 50]} initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
          sx={{ border: 'none' }} disableRowSelectionOnClick />
      </Card>

      <Dialog open={dialog} onClose={() => setDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editUser.id ? 'Edit User' : 'Add User'}</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Username" value={editUser.username || ''} onChange={(e) => setEditUser({ ...editUser, username: e.target.value })} margin="normal" />
          <TextField fullWidth label="Email" type="email" value={editUser.email || ''} onChange={(e) => setEditUser({ ...editUser, email: e.target.value })} margin="normal" />
          <TextField fullWidth label="Password" type="password" value={editUser.password || ''} onChange={(e) => setEditUser({ ...editUser, password: e.target.value })} margin="normal" helperText={editUser.id ? 'Leave blank to keep current' : 'Required'} />
          <FormControl fullWidth margin="normal">
            <InputLabel>Role</InputLabel>
            <Select value={editUser.role_name || 'viewer'} onChange={(e) => setEditUser({ ...editUser, role_name: e.target.value })} label="Role">
              <MenuItem value="admin">Admin</MenuItem>
              <MenuItem value="manager">Manager</MenuItem>
              <MenuItem value="viewer">Viewer</MenuItem>
            </Select>
          </FormControl>
          {editUser.id && <FormControlLabel control={<Switch checked={editUser.is_active ?? true} onChange={(e) => setEditUser({ ...editUser, is_active: e.target.checked })} />} label="Active" />}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave}>{editUser.id ? 'Update' : 'Create'}</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
