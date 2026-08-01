'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Box, Typography, Card, CardContent, Chip, IconButton, CircularProgress, Grid, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';
import { ArrowBack, Refresh } from '@mui/icons-material';
import api from '@/lib/api';

export default function ActionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetch = async () => {
    setLoading(true);
    try {
      const { data: d } = await api.get(`v1/actions/${params.id}/details`);
      setData(d);
    } catch { setData(null); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetch(); }, [params.id]);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>;
  if (!data?.action) return <Typography>Action not found</Typography>;

  const a = data.action;
  const urgencyColors: Record<string, string> = { high: '#F44336', medium: '#FF9800', low: '#4CAF50' };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => router.push('/actions')}><ArrowBack /></IconButton>
        <Box sx={{ flex: 1 }}><Typography variant="h5">{a.action}</Typography></Box>
        <IconButton onClick={fetch}><Refresh /></IconButton>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Box><Typography variant="caption">Person</Typography><Chip label={a.person} size="small" color="primary" /></Box>
          <Box><Typography variant="caption">Urgency</Typography><Chip label={a.urgency || 'medium'} size="small" sx={{ bgcolor: urgencyColors[a.urgency] || '#9E9E9E', color: 'white' }} /></Box>
          <Box><Typography variant="caption">Category</Typography><Chip label={a.category || '-'} size="small" variant="outlined" /></Box>
        </CardContent>
      </Card>

      <Grid container spacing={2} mb={3}>
        {data.report && (
          <Grid item xs={12} md={6}>
            <Card variant="outlined" sx={{ cursor: 'pointer' }} onClick={() => router.push(`/reports/${data.report.id}`)}>
              <CardContent>
                <Typography variant="caption" color="text.secondary">Report</Typography>
                <Typography variant="body2" fontWeight={600} color="primary">{data.report.date}</Typography>
                <Typography variant="caption">{data.report.subject}</Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
        {data.related_actions?.length > 0 && (
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="caption" color="text.secondary">Related Actions (same report)</Typography>
                {data.related_actions.map((r: any, i: number) => (
                  <Box key={i} sx={{ display: 'flex', gap: 1, alignItems: 'center', mt: 0.5 }}>
                    <Chip label={r.person} size="small" color="primary" variant="outlined" />
                    <Typography variant="body2">{r.action}</Typography>
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {data.occurrences?.length > 0 && (
        <>
          <Typography variant="h6" mb={2}>All Actions by {a.person} ({data.occurrences.length})</Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Action</TableCell>
                  <TableCell>Urgency</TableCell>
                  <TableCell>Report</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.occurrences.map((o: any) => (
                  <TableRow key={o.id} hover sx={{ cursor: 'pointer' }} onClick={() => router.push(`/reports/${o.report_id}`)}>
                    <TableCell>{o.report_date}</TableCell>
                    <TableCell>{o.action}</TableCell>
                    <TableCell><Chip label={o.urgency || 'medium'} size="small" sx={{ bgcolor: urgencyColors[o.urgency] || '#9E9E9E', color: 'white', height: 20, fontSize: 10 }} /></TableCell>
                    <TableCell>{o.subject || `#${o.report_id}`}</TableCell>
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
