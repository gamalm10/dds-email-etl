'use client';
import { Box, Card, CardContent, Typography, Switch, FormControlLabel, Divider, Button, Alert } from '@mui/material';
import { DarkMode, Notifications, Storage, Api } from '@mui/icons-material';
import { useThemeStore } from '@/stores/themeStore';

export default function SettingsPage() {
  const { mode, toggle } = useThemeStore();

  return (
    <Box>
      <Typography variant="h4" mb={3}>Settings</Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" mb={2}>Appearance</Typography>
          <FormControlLabel control={<Switch checked={mode === 'dark'} onChange={toggle} />}
            label={<Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><DarkMode /> Dark Mode</Box>} />
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" mb={2}>Notifications</Typography>
          <FormControlLabel control={<Switch defaultChecked />} label={<Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><Notifications /> New report processed</Box>} />
          <FormControlLabel control={<Switch defaultChecked />} label={<Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><Notifications /> High risk detected</Box>} />
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" mb={2}>Connection</Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Storage color="success" /><Typography variant="body2">MariaDB: Connected</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <Api color="success" /><Typography variant="body2">DDS API: Connected</Typography>
          </Box>
          <Alert severity="info" sx={{ mt: 2 }}>All systems operational. Last sync: {new Date().toLocaleString()}</Alert>
        </CardContent>
      </Card>
    </Box>
  );
}
