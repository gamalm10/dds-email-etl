'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Box, Typography, Card, CardContent, Chip, IconButton, CircularProgress, Grid, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';
import { ArrowBack, Refresh } from '@mui/icons-material';
import api from '@/lib/api';

export default function TaskDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetch = async () => {
    setLoading(true);
    try {
      const { data: d } = await api.get(`v1/tasks/${params.id}/details`);
      setData(d);
    } catch { setData(null); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetch(); }, [params.id]);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>;
  if (!data?.task) return <Typography>Task not found</Typography>;

  const t = data.task;
  const b = data.brand;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => router.push('/tasks')}><ArrowBack /></IconButton>
        <Box sx={{ flex: 1 }}><Typography variant="h5">{t.description}</Typography>
          {b?.brand_category && <Typography variant="body2" color="text.secondary" sx={{ cursor: 'pointer', color: 'primary.main' }} onClick={() => router.push(`/brands/${b.id}`)}>{b.division} / {b.brand_category}</Typography>}
        </Box>
        <IconButton onClick={fetch}><Refresh /></IconButton>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Box><Typography variant="caption">Assignee</Typography><Chip label={t.assigned_to || '-'} size="small" color="primary" /></Box>
          <Box><Typography variant="caption">Priority</Typography><Chip label={t.priority} size="small" color={t.priority === 'high' ? 'error' : 'warning'} /></Box>
          <Box><Typography variant="caption">Status</Typography>{t.is_resolved ? <Chip label="Done" size="small" color="success" /> : <Chip label="Open" size="small" color="warning" />}</Box>
          {t.is_overdue && <Chip label="Overdue" size="small" color="error" />}
          {t.is_blocked && <Chip label="Blocked" size="small" color="error" />}
          <Box><Typography variant="caption">Seen in</Typography><Chip label={`${t.occurrence_count || 1} reports`} size="small" variant="outlined" /></Box>
        </CardContent>
      </Card>

      <Grid container spacing={2} mb={3}>
        <Grid item xs={6} md={3}><Typography variant="caption">Request Date</Typography><Typography variant="body2">{t.request_date || '-'}</Typography></Grid>
        <Grid item xs={6} md={3}><Typography variant="caption">Deadline</Typography><Typography variant="body2">{t.deadline || t.deadline_text || '-'}</Typography></Grid>
        <Grid item xs={6} md={3}><Typography variant="caption">Category</Typography><Typography variant="body2">{t.category || '-'}</Typography></Grid>
        <Grid item xs={6} md={3}><Typography variant="caption">Brand/Category</Typography><Typography variant="body2" sx={{ cursor: 'pointer', color: 'primary.main' }} onClick={() => b?.id && router.push(`/brands/${b.id}`)}>{b?.brand_category || '-'}</Typography></Grid>
      </Grid>

      {data.occurrence_reports?.length > 0 && (
        <>
          <Typography variant="h6" mb={2}>Report Appearances</Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Report</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.occurrence_reports.map((r: any) => (
                  <TableRow key={r.report_id} hover sx={{ cursor: 'pointer' }} onClick={() => router.push(`/reports/${r.report_id}`)}>
                    <TableCell>{r.report_date}</TableCell>
                    <TableCell>{r.subject || `#${r.report_id}`}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Box>
  );
}
