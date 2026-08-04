'use client';
import { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import {
  Box, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, AppBar, Toolbar,
  Typography, IconButton, Avatar, Menu, MenuItem, Divider, Badge, Tooltip,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField, Button, Alert, CircularProgress,
} from '@mui/material';
import {
  Menu as MenuIcon,   Dashboard, Assessment, People, Settings, Logout,
  LightMode, DarkMode, Notifications, Category, TaskAlt, Insights as InsightsIcon, AssignmentTurnedIn, Preview,
  Lock, Store,
} from '@mui/icons-material';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { createTheme } from '@mui/material/styles';
import { useAuthStore } from '@/stores/authStore';
import api from '@/lib/api';
import { useThemeStore } from '@/stores/themeStore';
import { useNotificationStore } from '@/stores/notificationStore';
import SSEProvider from '@/components/common/SSEProvider';
import { lightTheme, darkTheme } from '@/lib/theme';

const DRAWER_WIDTH = 260;

const navItems = [
  { text: 'Dashboard', icon: <Dashboard />, path: '/' },
  { text: 'Vendors', icon: <Store />, path: '/vendors' },
  { text: 'Brand/Category', icon: <Category />, path: '/brands' },
  { text: 'Reports', icon: <Assessment />, path: '/reports' },
  { text: 'Review', icon: <Preview />, path: '/review' },
  { text: 'Insights', icon: <InsightsIcon />, path: '/insights' },
  { text: 'Actions', icon: <AssignmentTurnedIn />, path: '/actions' },
  { text: 'Tasks', icon: <TaskAlt />, path: '/tasks' },
  { text: 'Notifications', icon: <Notifications />, path: '/notifications' },
  { text: 'Users', icon: <People />, path: '/users', adminOnly: true },
  { text: 'Settings', icon: <Settings />, path: '/settings' },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const { user, logout } = useAuthStore();
  const { mode, toggle } = useThemeStore();
  const { unreadCount } = useNotificationStore();

  const [passwordDialog, setPasswordDialog] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [changingPass, setChangingPass] = useState(false);

  const validatePassword = (pw: string): string | null => {
    if (pw.length < 8) return 'Min 8 characters';
    if (!/[A-Z]/.test(pw)) return 'Need 1 uppercase';
    if (!/[0-9]/.test(pw)) return 'Need 1 number';
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(pw)) return 'Need 1 special char';
    return null;
  };

  const handleChangePassword = async () => {
    setPasswordError('');
    if (newPassword !== confirmPassword) {
      setPasswordError('Passwords do not match');
      return;
    }
    const v = validatePassword(newPassword);
    if (v) { setPasswordError(v); return; }
    setChangingPass(true);
    try {
      await api.post('v1/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordDialog(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      alert('Password changed. You will be logged out.');
      logout();
      router.push('/login');
    } catch (err: any) {
      setPasswordError(err.response?.data?.detail || 'Failed');
    } finally {
      setChangingPass(false);
    }
  };
  const theme = createTheme(mode === 'dark' ? darkTheme : lightTheme);

  const handleLogout = async () => {
    try { await fetch('/api/auth/logout', { method: 'POST', body: JSON.stringify({ refreshToken: useAuthStore.getState().refreshToken }) }); } catch {}
    logout();
    router.push('/login');
  };

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1, bgcolor: mode === 'dark' ? 'white' : 'transparent', borderRadius: mode === 'dark' ? 1 : 0 }}>
        <Box component="img" src="/logo.png" alt="A-part" sx={{ height: 'auto', maxHeight: 40, maxWidth: '100%', objectFit: 'contain', display: 'block', mx: 'auto' }} />
        <Typography variant="h6" fontWeight={700} sx={{ fontSize: '0.95rem', textAlign: 'center', color: mode === 'dark' ? 'black' : 'inherit' }}>
          DDS Operation
        </Typography>
      </Box>
      <Divider />
      <List sx={{ flex: 1, px: 1 }}>
        {navItems
          .filter((item) => !item.adminOnly || user?.role_name === 'admin')
          .map((item) => (
            <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                selected={pathname === item.path}
                onClick={() => { router.push(item.path); setMobileOpen(false); }}
                sx={{ borderRadius: 2, '&.Mui-selected': { bgcolor: 'primary.main', color: 'white', '&:hover': { bgcolor: 'primary.dark' } } }}
              >
                <ListItemIcon sx={{ minWidth: 40, color: pathname === item.path ? 'white' : undefined }}>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          ))}
      </List>
      <Divider />
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main', fontSize: 14 }}>{user?.username?.[0]}</Avatar>
        <Box sx={{ flex: 1 }}>
          <Typography variant="body2" fontWeight={600}>{user?.username}</Typography>
          <Typography variant="caption" color="text.secondary">{user?.role_name}</Typography>
        </Box>
      </Box>
    </Box>
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', minHeight: '100vh' }}>
        <AppBar position="fixed" sx={{ width: { md: `calc(100% - ${DRAWER_WIDTH}px)` }, ml: { md: `${DRAWER_WIDTH}px` }, bgcolor: 'background.paper', color: 'text.primary', boxShadow: 'none', borderBottom: 1, borderColor: 'divider' }} elevation={0}>
          <Toolbar>
            <IconButton edge="start" onClick={() => setMobileOpen(!mobileOpen)} sx={{ display: { md: 'none' } }}><MenuIcon /></IconButton>
            <Typography variant="h6" noWrap sx={{ flexGrow: 1, fontWeight: 600 }}>
              {navItems.find((i) => i.path === pathname)?.text || 'Dashboard'}
            </Typography>
            <Tooltip title={unreadCount > 0 ? `${unreadCount} notifications` : 'No notifications'}>
              <IconButton onClick={() => router.push('/notifications')}>
                <Badge badgeContent={unreadCount} color="error"><Notifications /></Badge>
              </IconButton>
            </Tooltip>
            <IconButton onClick={toggle} sx={{ ml: 1 }}>
              {mode === 'dark' ? <LightMode /> : <DarkMode />}
            </IconButton>
            <IconButton onClick={(e) => setAnchorEl(e.currentTarget)} sx={{ ml: 1 }}>
              <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main', fontSize: 14 }}>{user?.username?.[0]}</Avatar>
            </IconButton>
            <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={() => setAnchorEl(null)}>
              <MenuItem onClick={() => { setAnchorEl(null); router.push('/settings'); }}><ListItemIcon><Settings fontSize="small" /></ListItemIcon> Settings</MenuItem>
              <MenuItem onClick={() => { setAnchorEl(null); setPasswordDialog(true); }}><ListItemIcon><Lock fontSize="small" /></ListItemIcon> Change Password</MenuItem>
              <Divider />
              <MenuItem onClick={handleLogout}><ListItemIcon><Logout fontSize="small" /></ListItemIcon> Logout</MenuItem>
            </Menu>

            <Dialog open={passwordDialog} onClose={() => setPasswordDialog(false)} maxWidth="sm" fullWidth>
              <DialogTitle>Change Password</DialogTitle>
              <DialogContent>
                {passwordError && <Alert severity="error" sx={{ mb: 2 }}>{passwordError}</Alert>}
                <TextField fullWidth label="Current Password" type="password" margin="normal" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
                <TextField fullWidth label="New Password" type="password" margin="normal" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} error={newPassword.length > 0 && !!validatePassword(newPassword)} helperText={newPassword.length > 0 ? validatePassword(newPassword) || 'Min 8 chars, 1 uppercase, 1 number, 1 special char' : 'Min 8 chars, 1 uppercase, 1 number, 1 special char'} />
                <TextField fullWidth label="Confirm New Password" type="password" margin="normal" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} error={confirmPassword.length > 0 && confirmPassword !== newPassword} helperText={confirmPassword.length > 0 && confirmPassword !== newPassword ? 'Passwords do not match' : ''} />
              </DialogContent>
              <DialogActions>
                <Button onClick={() => setPasswordDialog(false)}>Cancel</Button>
                <Button variant="contained" disabled={!currentPassword || !newPassword || !confirmPassword || changingPass} startIcon={changingPass ? <CircularProgress size={16} color="inherit" /> : null} onClick={handleChangePassword}>Change Password</Button>
              </DialogActions>
            </Dialog>
          </Toolbar>
        </AppBar>

        <Box component="nav" sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}>
          <Drawer variant="temporary" open={mobileOpen} onClose={() => setMobileOpen(false)}
            ModalProps={{ keepMounted: true }} sx={{ display: { xs: 'block', md: 'none' }, '& .MuiDrawer-paper': { width: DRAWER_WIDTH } }}>
            {drawer}
          </Drawer>
          <Drawer variant="permanent" sx={{ display: { xs: 'none', md: 'block' }, '& .MuiDrawer-paper': { width: DRAWER_WIDTH, borderRight: 1, borderColor: 'divider' } }} open>
            {drawer}
          </Drawer>
        </Box>

        <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8, bgcolor: 'background.default', minHeight: '100vh' }}>
          <SSEProvider>{children}</SSEProvider>
        </Box>
      </Box>
    </ThemeProvider>
  );
}
