'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Box, Typography, Card, CardContent, Tabs, Tab, Chip, IconButton, CircularProgress,
  Grid, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
} from '@mui/material';
import { ArrowBack, Refresh } from '@mui/icons-material';
import api from '@/lib/api';
import InsightTimeline from '@/components/insights/InsightTimeline';

export default function BrandDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [insightTimeline, setInsightTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState(0);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const id = params.id as string;
      const [dRes, hRes, tRes, itRes] = await Promise.all([
        api.get(`v1/brands/${id}/details`).then(({ data }) => data || {}).catch(() => ({})),
        api.get(`v1/brands/${id}/history`).then(({ data }) => data || {}).catch(() => ({})),
        api.get(`v1/brands/${id}/timeline`).then(({ data }) => data || []).catch(() => []),
        api.get(`v1/brands/${id}/insights/timeline`).then(({ data }) => data || []).catch(() => []),
      ]);
      setData(dRes || {});
      setHistory(Array.isArray(hRes?.history) ? hRes.history : []);
      setTimeline(Array.isArray(tRes) ? tRes : []);
      setInsightTimeline(Array.isArray(itRes) ? itRes : []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, [params.id]);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>;
  if (!data?.brand) return <Typography>Brand not found</Typography>;

  const brand = data.brand;
  const getStatusColor = (s: string) => {
    const colors: Record<string, string> = { green: '#4CAF50', yellow: '#FF9800', red: '#F44336', grey: '#9E9E9E', unknown: '#E0E0E0' };
    return colors[s] || '#9E9E9E';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => router.push('/brands')}><ArrowBack /></IconButton>
        <Box sx={{ flex: 1 }}><Typography variant="h5">{brand.brand_category}</Typography>
          <Typography variant="body2" color="text.secondary">{brand.division} · {data.report_count} reports</Typography>
        </Box>
        <IconButton onClick={fetchAll}><Refresh /></IconButton>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          {data.items.length > 0 && (
            <Chip label={data.items[0].availability_status} size="small" sx={{ bgcolor: getStatusColor(data.items[0].availability_status), color: 'white' }} />
          )}
          <Chip label={`${data.report_count} Reports`} size="small" variant="outlined" />
          <Chip label={`${data.tasks.length} Tasks`} size="small" variant="outlined" />
          <Chip label={`${data.insights.length} Insights`} size="small" variant="outlined" />
          <Chip label={`${data.payments.length} Payments`} size="small" variant="outlined" />
        </CardContent>
      </Card>

      <Card>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
          <Tab label="Overview" />
          <Tab label="History" />
          <Tab label="Timeline" />
          <Tab label="Tasks" />
          <Tab label="Insights" />
          <Tab label="Insights Timeline" />
        </Tabs>

        {tab === 0 && (
          <Box sx={{ p: 2 }}>
            <Grid container spacing={2} mb={3}>
              <Grid item xs={6} md={3}><Typography variant="caption">Brand/Category</Typography><Typography variant="body2" fontWeight={600}>{brand.brand_category}</Typography></Grid>
              <Grid item xs={6} md={3}><Typography variant="caption">Division</Typography><Typography variant="body2">{brand.division}</Typography></Grid>
              <Grid item xs={6} md={3}><Typography variant="caption">Reports</Typography><Typography variant="h6">{data.report_count}</Typography></Grid>
              <Grid item xs={6} md={3}><Typography variant="caption">Open Tasks</Typography><Typography variant="h6">{data.tasks.filter((t:any) => !t.is_resolved).length}</Typography></Grid>
            </Grid>
            {data.items.length > 0 && (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>Latest Report Item</Typography>
                <Grid container spacing={1}>
                  <Grid item xs={4}><Typography variant="caption">Status:</Typography> <Chip label={data.items[0].availability_status} size="small" sx={{ bgcolor: getStatusColor(data.items[0].availability_status), color: 'white' }} /></Grid>
                  <Grid item xs={4}><Typography variant="caption">Milestone:</Typography> {data.items[0].milestone || '-'}</Grid>
                  <Grid item xs={4}><Typography variant="caption">Vendor:</Typography> {data.items[0].vendor || '-'}</Grid>
                  <Grid item xs={12}><Typography variant="caption">Shipment:</Typography> {data.items[0].shipment_bis || '-'}</Grid>
                  <Grid item xs={12}><Typography variant="caption">Comments:</Typography> {data.items[0].comments_actions || '-'}</Grid>
                </Grid>
              </Paper>
            )}
          </Box>
        )}

        {tab === 1 && (
          <Box sx={{ p: 2 }}>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Milestone</TableCell>
                    <TableCell>Shipment</TableCell>
                    <TableCell>Comments</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {history.map((h: any) => (
                    <TableRow key={h.item_id} hover sx={{ cursor: 'pointer' }} onClick={() => router.push(`/reports/${h.report_id}`)}>
                      <TableCell>{h.report_date}</TableCell>
                      <TableCell><Chip label={h.availability_status} size="small" sx={{ bgcolor: getStatusColor(h.availability_status), color: 'white' }} /></TableCell>
                      <TableCell>{h.milestone || '-'}</TableCell>
                      <TableCell>{h.shipment_bis || '-'}</TableCell>
                      <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>{h.comments_actions || '-'}</TableCell>
                    </TableRow>
                  ))}
                  {history.length === 0 && <TableRow><TableCell colSpan={5} align="center">No history available</TableCell></TableRow>}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {tab === 2 && (
          <Box sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {timeline.map((e: any, i: number) => (
                <Box key={i} sx={{ display: 'flex', gap: 2, pb: 2, borderLeft: i < timeline.length - 1 ? '2px solid' : 'none', borderColor: 'primary.main', pl: 2, ml: 1 }}>
                  <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: getStatusColor(e.status), mt: 0.5, flexShrink: 0 }} />
                  <Box>
                    <Typography variant="body2" fontWeight={600}>{e.date}</Typography>
                    <Typography variant="body2">Status: <Chip label={e.status} size="small" sx={{ bgcolor: getStatusColor(e.status), color: 'white' }} /></Typography>
                    {e.milestone && <Typography variant="body2">Milestone: {e.milestone}</Typography>}
                    {e.shipment && <Typography variant="body2">Shipment: {e.shipment}</Typography>}
                    {e.comments && <Typography variant="caption" color="text.secondary">{e.comments}</Typography>}
                  </Box>
                </Box>
              ))}
              {timeline.length === 0 && <Typography color="text.secondary">No timeline events</Typography>}
            </Box>
          </Box>
        )}

        {tab === 3 && (
          <Box sx={{ p: 2 }}>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Task</TableCell>
                    <TableCell>Assignee</TableCell>
                    <TableCell>Category</TableCell>
                    <TableCell>Priority</TableCell>
                    <TableCell>Deadline</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.tasks.map((t: any) => (
                    <TableRow key={t.id} hover sx={{ cursor: 'pointer' }} onClick={() => router.push(`/tasks/${t.id}`)}>
                      <TableCell>{t.description}</TableCell>
                      <TableCell>{t.assigned_to || '-'}</TableCell>
                      <TableCell>{t.category || '-'}</TableCell>
                      <TableCell><Chip label={t.priority} size="small" color={t.priority === 'high' ? 'error' : t.priority === 'low' ? 'default' : 'warning'} /></TableCell>
                      <TableCell>{t.deadline || '-'}</TableCell>
                      <TableCell>{t.is_resolved ? <Chip label="Done" size="small" color="success" /> : <Chip label="Open" size="small" color="warning" />}</TableCell>
                    </TableRow>
                  ))}
                  {data.tasks.length === 0 && <TableRow><TableCell colSpan={6} align="center">No tasks</TableCell></TableRow>}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {tab === 4 && (
          <Box sx={{ p: 2 }}>
            {data.insights.map((ins: any) => (
              <Card key={ins.id} variant="outlined" sx={{ mb: 1 }}>
                <CardContent sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, py: '8px !important' }}>
                  <Chip label={ins.severity} size="small" color={ins.severity === 'critical' ? 'error' : ins.severity === 'major' ? 'warning' : 'default'} />
                  <Box>
                    <Typography variant="body2">{ins.description}</Typography>
                    {ins.impact && <Typography variant="caption" color="text.secondary">Impact: {ins.impact}</Typography>}
                  </Box>
                </CardContent>
              </Card>
            ))}
            {data.insights.length === 0 && <Typography color="text.secondary">No insights</Typography>}
          </Box>
        )}

        {tab === 5 && (
          <Box sx={{ p: 2 }}>
            <InsightTimeline events={insightTimeline} />
          </Box>
        )}
      </Card>
    </Box>
  );
}
