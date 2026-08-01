'use client';
import { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import {
  Box, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, AppBar, Toolbar,
  Typography, IconButton, Avatar, Menu, MenuItem, Divider, Badge, Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon, Dashboard, Assessment, CloudUpload, People, Settings, Logout,
  LightMode, DarkMode, Notifications, Inventory2,
} from '@mui/icons-material';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { createTheme } from '@mui/material/styles';
import { useAuthStore } from '@/stores/authStore';
import { useThemeStore } from '@/stores/themeStore';
import { useNotificationStore } from '@/stores/notificationStore';
import SSEProvider from '@/components/common/SSEProvider';
import { lightTheme, darkTheme } from '@/lib/theme';

const DRAWER_WIDTH = 260;

const navItems = [
  { text: 'Dashboard', icon: <Dashboard />, path: '/' },
  { text: 'Brands', icon: <Inventory2 />, path: '/brands' },
  { text: 'Reports', icon: <Assessment />, path: '/reports' },
  { text: 'Upload Email', icon: <CloudUpload />, path: '/upload' },
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
  const theme = createTheme(mode === 'dark' ? darkTheme : lightTheme);

  const handleLogout = async () => {
    try { await fetch('/api/auth/logout', { method: 'POST', body: JSON.stringify({ refreshToken: useAuthStore.getState().refreshToken }) }); } catch {}
    logout();
    router.push('/login');
  };

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2.5, display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Inventory2 color="primary" />
        <Typography variant="h6" fontWeight={700}>DDS Platform</Typography>
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
              <Divider />
              <MenuItem onClick={handleLogout}><ListItemIcon><Logout fontSize="small" /></ListItemIcon> Logout</MenuItem>
            </Menu>
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
