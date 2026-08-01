'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Box, Typography, Card, CardContent, Chip, IconButton, CircularProgress, Grid } from '@mui/material';
import { ArrowBack, Refresh } from '@mui/icons-material';
import api from '@/lib/api';

export default function InsightDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetch = async () => {
    setLoading(true);
    try {
      const { data: d } = await api.get(`v1/insights/${params.id}/details`);
      setData(d);
    } catch { setData(null); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetch(); }, [params.id]);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>;
  if (!data?.insight) return <Typography>Insight not found</Typography>;

  const ins = data.insight;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => router.back()}><ArrowBack /></IconButton>
        <Box sx={{ flex: 1 }}><Typography variant="h5">Insight Details</Typography></Box>
        <IconButton onClick={fetch}><Refresh /></IconButton>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
            {ins.severity && <Chip label={ins.severity} size="small" color={ins.severity === 'critical' ? 'error' : ins.severity === 'major' ? 'warning' : 'default'} />}
            {ins.insight_type && <Chip label={ins.insight_type} size="small" variant="outlined" />}
            {ins.anomaly_score && <Chip label={`Anomaly: ${ins.anomaly_score}`} size="small" color="warning" variant="outlined" />}
          </Box>
          <Typography variant="h6" mb={1}>{ins.description || '(no description)'}</Typography>
          {ins.impact && <Typography variant="body2" color="text.secondary" mb={1}>Impact: {ins.impact}</Typography>}
          {ins.recommendation && <Typography variant="body2" color="success.main">Recommendation: {ins.recommendation}</Typography>}
        </CardContent>
      </Card>

      <Grid container spacing={2} mb={3}>
        {data.brand && (
          <Grid item xs={12} md={6}>
            <Card variant="outlined" sx={{ cursor: 'pointer' }} onClick={() => router.push(`/brands/${data.brand.id}`)}>
              <CardContent>
                <Typography variant="caption" color="text.secondary">Brand/Category</Typography>
                <Typography variant="body2" fontWeight={600} color="primary">{data.brand.brand_category}</Typography>
                <Typography variant="caption">{data.brand.division}</Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
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
      </Grid>

      {ins.risk_tags && (
        <Card variant="outlined" sx={{ mb: 3, p: 2 }}>
          <Typography variant="subtitle2" mb={1}>Risk Tags</Typography>
          {(() => {
            try {
              return JSON.parse(ins.risk_tags).map((tag: string) => (
                <Chip key={tag} label={tag} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
              ));
            } catch { return <Typography variant="body2">{ins.risk_tags}</Typography>; }
          })()}
        </Card>
      )}

      {data.anomalies?.length > 0 && (
        <Card variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle2" mb={1}>Related Anomalies ({data.anomalies.length})</Typography>
          {data.anomalies.map((a: any) => (
            <Chip key={a.id} label={`Score: ${a.similarity_score}`} size="small" color="warning" variant="outlined" sx={{ mr: 0.5, mb: 0.5 }} />
          ))}
        </Card>
      )}
    </Box>
  );
}
