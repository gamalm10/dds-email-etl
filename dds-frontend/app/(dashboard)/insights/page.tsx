'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Typography, Card, Chip, CircularProgress, ToggleButtonGroup, ToggleButton, IconButton } from '@mui/material';
import { Refresh } from '@mui/icons-material';
import api from '@/lib/api';
import InsightCard from '@/components/insights/InsightCard';

const SEVERITIES = ['all', 'critical', 'major', 'minor', 'info'];

export default function InsightsPage() {
  const router = useRouter();
  const [insights, setInsights] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [sevFilter, setSevFilter] = useState('all');

  const fetch = async () => {
    setLoading(true);
    try {
      const params = sevFilter !== 'all' ? `?severity=${sevFilter}` : '';
      const { data } = await api.get(`v1/insights${params}`);
      setInsights(Array.isArray(data) ? data : []);
    } catch { setInsights([]); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetch(); }, [sevFilter]);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Insights <Chip label={insights.length} size="small" color="warning" /></Typography>
        <IconButton onClick={fetch}><Refresh /></IconButton>
      </Box>
      <Card sx={{ mb: 3, p: 2 }}>
        <ToggleButtonGroup value={sevFilter} exclusive onChange={(_, v) => v && setSevFilter(v)} size="small">
          {SEVERITIES.map(s => <ToggleButton key={s} value={s}>{s}</ToggleButton>)}
        </ToggleButtonGroup>
      </Card>
      {loading ? <CircularProgress /> : (
        insights.map((i) => <InsightCard key={i.id} insight={i} compact />)
      )}
      {!loading && insights.length === 0 && <Typography color="text.secondary">No insights found</Typography>}
    </Box>
  );
}
