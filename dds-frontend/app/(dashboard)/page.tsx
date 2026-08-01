'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box, Grid, Card, CardContent, Typography, Chip, IconButton,
} from '@mui/material';
import {
  Inventory2, AssignmentLate, Warning, TaskAlt, Refresh,
} from '@mui/icons-material';
import api from '@/lib/api';
import type { DashboardSummary, ReportSummary } from '@/types/report';

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dashRes, repRes] = await Promise.all([
        api.get('v1/dashboard/summary'),
        api.get('v1/reports'),
      ]);
      setDashboard(dashRes.data);
      setReports(repRes.data.slice(0, 5));
    } catch (err) {
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const statCards = dashboard ? [
    { label: 'Brands', value: dashboard.total_brands, icon: <Inventory2 />, color: 'primary' },
    { label: 'Issues', value: dashboard.brands_with_issues, icon: <Warning />, color: 'error' },
    { label: 'Open Tasks', value: dashboard.open_tasks, icon: <TaskAlt />, color: 'warning' },
    { label: 'Critical Insights', value: dashboard.critical_insights, icon: <AssignmentLate />, color: 'error' },
  ] : [];

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      completed: '#4CAF50', failed: '#F44336', processing: '#FF9800', pending: '#9E9E9E',
    };
    return colors[status] || '#9E9E9E';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Dashboard</Typography>
        <IconButton onClick={fetchData}><Refresh /></IconButton>
      </Box>

      <Grid container spacing={3} mb={4}>
        {statCards.map((card) => (
          <Grid item xs={12} sm={6} md={3} key={card.label}>
            <Card sx={{ cursor: 'pointer', transition: 'transform 0.2s', '&:hover': { transform: 'scale(1.02)' } }}
              onClick={() => {
                if (card.label === 'Issues') router.push('/dashboard/issues');
                else if (card.label === 'Open Tasks') router.push('/tasks');
                else if (card.label === 'Critical Insights') router.push('/dashboard/critical');
              }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 3 }}>
                <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: `${card.color}.main`, color: 'white', display: 'flex' }}>
                  {card.icon}
                </Box>
                <Box>
                  <Typography variant="h4" fontWeight={700}>{card.value}</Typography>
                  <Typography variant="body2" color="text.secondary">{card.label}</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" mb={2}>Recent Reports</Typography>
              {reports.map((r) => (
                <Box key={r.id} sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 1.5, borderBottom: '1px solid', borderColor: 'divider', cursor: 'pointer' }}
                  onClick={() => router.push(`/reports/${r.id}`)}>
                  <Chip label={r.processing_status} size="small" sx={{ bgcolor: getStatusColor(r.processing_status), color: 'white', minWidth: 80 }} />
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body2" fontWeight={600}>{r.subject || `Report #${r.id}`}</Typography>
                    <Typography variant="caption" color="text.secondary">{r.report_date} · {r.item_count} items · {r.task_count} tasks</Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">{r.created_at ? new Date(r.created_at).toLocaleDateString() : ''}</Typography>
                </Box>
              ))}
              {reports.length === 0 && !loading && (
                <Typography variant="body2" color="text.secondary" textAlign="center" py={4}>No reports yet. Upload an email to get started.</Typography>
              )}
              {loading && <Typography variant="body2" color="text.secondary" textAlign="center" py={4}>Loading...</Typography>}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" mb={2}>Status Distribution</Typography>
              {dashboard?.status_distribution && Object.entries(dashboard.status_distribution).map(([key, val]) => (
                <Box key={key} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: key === 'green' ? '#4CAF50' : key === 'yellow' ? '#FF9800' : key === 'red' ? '#F44336' : key === 'grey' ? '#9E9E9E' : '#E0E0E0' }} />
                  <Typography variant="body2" sx={{ flex: 1, textTransform: 'capitalize' }}>{key}</Typography>
                  <Typography variant="body2" fontWeight={600}>{val}</Typography>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
