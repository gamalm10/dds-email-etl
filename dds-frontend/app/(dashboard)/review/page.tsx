'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Card, CardContent, Typography } from '@mui/material';
import BrandSelector from '@/components/reviews/BrandSelector';
import BrandTimeline from '@/components/reviews/BrandTimeline';
import StatusChangeChart from '@/components/reviews/StatusChangeChart';
import InsightsPanel from '@/components/reviews/InsightsPanel';
import TasksPanel from '@/components/reviews/TasksPanel';

export default function ReviewPage() {
  const [selectedBrand, setSelectedBrand] = useState<{ id: number; division: string; brand_category: string } | null>(null);
  const [brandHistory, setBrandHistory] = useState<any>(null);
  const [crossInsights, setCrossInsights] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selectedBrand) return;
    setLoading(true);
    Promise.all([
      api.get(`v1/reports/brand-history/${selectedBrand.id}?limit=10`),
      api.get(`v1/reports/cross-report-insights?brand_id=${selectedBrand.id}`),
    ])
      .then(([historyRes, insightsRes]) => {
        setBrandHistory(historyRes.data);
        setCrossInsights(insightsRes.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedBrand]);

  return (
    <div style={{ padding: 24 }}>
      <Typography variant="h4" gutterBottom fontWeight={600}>
        Brand Review
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Review brand performance across reports — timeline, insights, and tasks.
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <BrandSelector value={selectedBrand} onChange={setSelectedBrand} />
        </CardContent>
      </Card>

      {selectedBrand && (
        <>
          <BrandTimeline history={brandHistory} loading={loading} />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginTop: 24 }}>
            <StatusChangeChart history={brandHistory} loading={loading} />
            <InsightsPanel insights={crossInsights} brandHistory={brandHistory} loading={loading} />
          </div>
          <div style={{ marginTop: 24 }}>
            <TasksPanel history={brandHistory} loading={loading} />
          </div>
        </>
      )}
    </div>
  );
}
