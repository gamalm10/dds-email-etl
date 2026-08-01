'use client';
import { useEffect, useState } from 'react';
import { Box, Typography, Chip, Card, CardContent, CircularProgress } from '@mui/material';
import { TrendingUp, TrendingDown, Add, Remove, CheckCircle, Warning } from '@mui/icons-material';

interface DeltaData {
  has_previous: boolean;
  previous_report_date?: string;
  improved: Array<{ brand_id: number; from: string; to: string }>;
  worsened: Array<{ brand_id: number; from: string; to: string }>;
  new_brands: Array<{ brand_id: number; status: string }>;
  removed_brands: Array<{ brand_id: number; status: string }>;
  new_risks?: string[];
  resolved_risks?: string[];
  supplier_updates?: Array<{ vendor: string; brand: string; from: string; to: string; status: string }>;
  task_changes?: { current_total: number; previous_total: number; new: number; resolved: number };
}

export default function DeltaSection({ reportId }: { reportId: number }) {
  const [delta, setDelta] = useState<DeltaData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/v1/reports/${reportId}/delta`).then(r => r.json()).then(d => { setDelta(d); setLoading(false); });
  }, [reportId]);

  if (loading) return <CircularProgress size={20} />;
  if (!delta?.has_previous) return null;

  const hasChanges = delta.improved.length > 0 || delta.worsened.length > 0 || delta.new_brands.length > 0
    || (delta.new_risks?.length || 0) > 0 || (delta.resolved_risks?.length || 0) > 0
    || (delta.supplier_updates?.length || 0) > 0;

  return (
    <Card variant="outlined" sx={{ mb: 3 }}>
      <CardContent sx={{ py: 1.5 }}>
        <Typography variant="subtitle2" mb={1} color="text.secondary">
          vs. previous report ({delta.previous_report_date})
        </Typography>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: hasChanges ? 1 : 0 }}>
          {delta.improved.length > 0 && (
            <Chip icon={<TrendingUp />} label={`${delta.improved.length} Improved`} size="small" color="success" variant="outlined" />
          )}
          {delta.worsened.length > 0 && (
            <Chip icon={<TrendingDown />} label={`${delta.worsened.length} Worsened`} size="small" color="error" variant="outlined" />
          )}
          {delta.new_brands.length > 0 && (
            <Chip icon={<Add />} label={`${delta.new_brands.length} New`} size="small" color="info" variant="outlined" />
          )}
          {delta.removed_brands.length > 0 && (
            <Chip icon={<Remove />} label={`${delta.removed_brands.length} Removed`} size="small" color="default" variant="outlined" />
          )}
        </Box>

        {delta.new_risks && delta.new_risks.length > 0 && (
          <Box sx={{ mt: 0.5 }}>
            <Typography variant="caption" color="text.secondary">New Issues</Typography>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
              {delta.new_risks.map((r) => (
                <Chip key={r} icon={<Warning />} label={r.replace(/_/g, ' ')} size="small" color="error" variant="outlined" />
              ))}
            </Box>
          </Box>
        )}

        {delta.resolved_risks && delta.resolved_risks.length > 0 && (
          <Box sx={{ mt: 0.5 }}>
            <Typography variant="caption" color="text.secondary">Resolved</Typography>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
              {delta.resolved_risks.map((r) => (
                <Chip key={r} icon={<CheckCircle />} label={r.replace(/_/g, ' ')} size="small" color="success" variant="outlined" />
              ))}
            </Box>
          </Box>
        )}

        {delta.supplier_updates && delta.supplier_updates.length > 0 && (
          <Box sx={{ mt: 0.5 }}>
            <Typography variant="caption" color="text.secondary">Supplier Updates</Typography>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
              {delta.supplier_updates.map((s, i: number) => (
                <Chip key={i} label={`${s.vendor}: ${s.from}→${s.to}`} size="small"
                  color={s.status === 'worsened' ? 'error' : 'success'} variant="outlined" />
              ))}
            </Box>
          </Box>
        )}

        {delta.task_changes && (
          <Box sx={{ mt: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              Tasks: {delta.task_changes.current_total} total
              {delta.task_changes.new > 0 && ` (+${delta.task_changes.new} new)`}
              {delta.task_changes.resolved > 0 && ` (-${delta.task_changes.resolved} resolved)`}
            </Typography>
          </Box>
        )}

        {!hasChanges && (
          <Typography variant="body2" color="text.secondary">No changes since last report</Typography>
        )}
      </CardContent>
    </Card>
  );
}
