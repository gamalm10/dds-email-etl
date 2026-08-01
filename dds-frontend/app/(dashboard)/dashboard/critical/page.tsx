'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Typography, Card, CardContent, Chip, CircularProgress, Alert } from '@mui/material';
import api from '@/lib/api';

export default function CriticalPage() {
  const router = useRouter();
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('v1/dashboard/critical').then(({ data }) => setItems(Array.isArray(data) ? data : [])).catch(() => setItems([])).finally(() => setLoading(false));
  }, []);

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Typography variant="h4">Critical Items</Typography>
        <Chip label={`${items.length} found`} color="error" size="small" />
      </Box>
      {loading ? <CircularProgress /> : (
        items.map((i) => (
          <Card key={i.item_id} variant="outlined" sx={{ mb: 1, borderColor: 'error.main' }}>
            <CardContent sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
              <Chip label="RED" size="small" color="error" />
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" fontWeight={600} sx={{ cursor: 'pointer', color: 'primary.main' }} onClick={() => router.push(`/brands/${i.brand_id}`)}>{i.brand_category}</Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                  <Typography variant="caption" color="text.secondary">Report: {i.report_date}</Typography>
                  {i.risk_score && <Chip label={`Risk: ${i.risk_score}`} size="small" color="error" variant="outlined" />}
                  <Typography variant="caption" sx={{ cursor: 'pointer', color: 'primary.main' }} onClick={() => router.push(`/reports/${i.report_id}`)}>View Report</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        ))
      )}
      {!loading && items.length === 0 && <Alert severity="success">No critical items</Alert>}
    </Box>
  );
}
