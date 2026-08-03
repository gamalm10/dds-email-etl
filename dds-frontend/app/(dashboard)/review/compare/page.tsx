'use client';

import { useState } from 'react';
import api from '@/lib/api';
import { Card, CardContent, Typography, Box } from '@mui/material';
import ReportSelector from '@/components/reviews/ReportSelector';
import ComparisonTable from '@/components/reviews/ComparisonTable';

export default function ComparePage() {
  const [report1, setReport1] = useState<number | null>(null);
  const [report2, setReport2] = useState<number | null>(null);
  const [comparison, setComparison] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleCompare = async () => {
    if (!report1 || !report2) return;
    setLoading(true);
    try {
      const res = await api.get(`v1/reports/compare?report_id_1=${report1}&report_id_2=${report2}`);
      setComparison(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <Typography variant="h4" gutterBottom fontWeight={600}>
        Report Comparison
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Compare two reports side-by-side to identify changes in status, milestones, and comments.
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <ReportSelector
            report1={report1}
            report2={report2}
            onChange1={setReport1}
            onChange2={setReport2}
            onCompare={handleCompare}
            loading={loading}
          />
        </CardContent>
      </Card>

      {comparison && (
        <ComparisonTable comparison={comparison} loading={loading} />
      )}
    </div>
  );
}
