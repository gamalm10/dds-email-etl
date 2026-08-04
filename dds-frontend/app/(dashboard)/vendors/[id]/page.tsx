'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Box, Typography, Card, CardContent, Chip, IconButton, CircularProgress,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
} from '@mui/material';
import { ArrowBack, Refresh, TrendingUp } from '@mui/icons-material';
import api from '@/lib/api';
import ReportTimeline, { getStatusColor } from '@/components/vendors/ReportTimeline';

export default function VendorOverviewPage() {
  const params = useParams();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const vendor = decodeURIComponent(params.id as string);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const { data } = await api.get(`v1/vendors/${encodeURIComponent(vendor)}/overview`);
      setData(data || {});
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, [params.id]);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>;
  if (!data?.vendor) return <Typography>Vendor not found</Typography>;

  const stats = data.stats || {};

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => router.push('/vendors')}><ArrowBack /></IconButton>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h5">{data.vendor}</Typography>
          <Typography variant="body2" color="text.secondary">{data.brands?.length || 0} brands · {stats.report_count} reports</Typography>
        </Box>
        <IconButton onClick={fetchAll}><Refresh /></IconButton>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          <Chip label={data.latest_status} size="small" sx={{ bgcolor: getStatusColor(data.latest_status), color: 'white' }} />
          <Chip label={`${stats.brand_count} Brands`} size="small" variant="outlined" />
          <Chip label={`${stats.report_count} Reports`} size="small" variant="outlined" />
          <Chip label={`${stats.open_tasks} Open Tasks`} size="small" variant="outlined" />
          <Chip label={`${stats.total_insights} Insights`} size="small" variant="outlined" />
        </CardContent>
      </Card>

      {data.brands?.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrendingUp color="primary" /> Brands/Categories Served
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Brand/Category</TableCell>
                    <TableCell>Division</TableCell>
                    <TableCell>Items</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.brands.map((b: any) => (
                    <TableRow key={b.brand_id} hover sx={{ cursor: 'pointer' }} onClick={() => router.push(`/brands/${b.brand_id}`)}>
                      <TableCell>{b.brand_category}</TableCell>
                      <TableCell>{b.division || '-'}</TableCell>
                      <TableCell>{b.count}</TableCell>
                      <TableCell><Chip label={b.latest_status} size="small" sx={{ bgcolor: getStatusColor(b.latest_status), color: 'white' }} /></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      <Typography variant="h6" gutterBottom>Report Timeline</Typography>
      <ReportTimeline reports={data.reports} />
    </Box>
  );
}
