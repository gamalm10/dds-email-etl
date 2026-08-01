'use client';
import { Box, Card, CardContent, Typography, Button, IconButton, Chip } from '@mui/material';
import { Delete, Check, Notifications as NotifIcon } from '@mui/icons-material';
import { useNotificationStore } from '@/stores/notificationStore';
import { useRouter } from 'next/navigation';

export default function NotificationsPage() {
  const { notifications, markRead, clearAll, markAllRead } = useNotificationStore();
  const router = useRouter();

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      REPORT_PROCESSED: '#4CAF50', RISK_DETECTED: '#F44336',
      TASK_OVERDUE: '#FF9800', CRITICAL_INSIGHT: '#F44336',
    };
    return colors[type] || '#9E9E9E';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Notifications</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button size="small" onClick={markAllRead} startIcon={<Check />}>Mark All Read</Button>
          <Button size="small" onClick={clearAll} startIcon={<Delete />} color="error">Clear All</Button>
        </Box>
      </Box>

      {notifications.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 8 }}>
            <NotifIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">No notifications yet</Typography>
            <Typography variant="body2" color="text.disabled">Notifications will appear here when reports are processed</Typography>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent sx={{ p: 0 }}>
            {notifications.map((n) => (
              <Box key={n.id} sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2, borderBottom: '1px solid', borderColor: 'divider',
                bgcolor: n.read ? 'transparent' : 'action.hover', cursor: n.reportId ? 'pointer' : 'default' }}
                onClick={() => { markRead(n.id); if (n.reportId) router.push(`/reports/${n.reportId}`); }}>
                <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: getTypeColor(n.type), flexShrink: 0 }} />
                <Box sx={{ flex: 1 }}>
                  <Typography variant="body2" fontWeight={600}>{n.title}</Typography>
                  <Typography variant="caption" color="text.secondary">{n.message}</Typography>
                </Box>
                <Chip label={n.type.replace(/_/g, ' ')} size="small" sx={{ bgcolor: getTypeColor(n.type), color: 'white' }} />
                <Typography variant="caption" color="text.disabled">{n.timestamp.toLocaleTimeString()}</Typography>
                {!n.read && <IconButton size="small" onClick={(e) => { e.stopPropagation(); markRead(n.id); }}><Check fontSize="small" /></IconButton>}
              </Box>
            ))}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
