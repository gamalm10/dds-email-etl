'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Typography, Card, CardContent, Chip, CircularProgress } from '@mui/material';

export default function IssuesPage() {
  const router = useRouter();
  const [issues, setIssues] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/v1/dashboard/issues').then(r => r.json()).then(d => setIssues(Array.isArray(d) ? d : [])).finally(() => setLoading(false));
  }, []);

  const getSeverityColor = (s: string) => {
    const c: Record<string, string> = { critical: '#F44336', major: '#FF9800', minor: '#2196F3', info: '#9E9E9E' };
    return c[s] || '#9E9E9E';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Typography variant="h4">Issues</Typography>
        <Chip label={`${issues.length} found`} color="warning" size="small" />
      </Box>
      {loading ? <CircularProgress /> : (
        issues.map((i) => (
          <Card key={i.insight_id} variant="outlined" sx={{ mb: 1, cursor: 'pointer' }} onClick={() => router.push(`/reports/${i.report_id}`)}>
            <CardContent sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
              <Chip label={i.severity} size="small" sx={{ bgcolor: getSeverityColor(i.severity), color: 'white' }} />
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" fontWeight={600}>{i.description}</Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                  <Typography variant="caption" sx={{ cursor: 'pointer', color: 'primary.main' }} onClick={(e) => { e.stopPropagation(); router.push(`/brands/${i.brand_id}`); }}>{i.brand_category} / {i.division}</Typography>
                  <Typography variant="caption" color="text.secondary">Report: {i.report_date}</Typography>
                  {i.risk_score && <Chip label={`Risk: ${i.risk_score}`} size="small" color="error" variant="outlined" />}
                </Box>
              </Box>
            </CardContent>
          </Card>
        ))
      )}
    </Box>
  );
}
