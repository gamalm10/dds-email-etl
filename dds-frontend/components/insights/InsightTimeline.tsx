'use client';
import { Box, Typography, Chip } from '@mui/material';
import { useRouter } from 'next/navigation';

interface TimelineEvent {
  id: number;
  type?: string | null;
  description?: string;
  severity?: string | null;
  report_id: number;
  report_date?: string | null;
  impact?: string | null;
}

interface InsightTimelineProps {
  events: TimelineEvent[];
}

const severityColors: Record<string, string> = {
  critical: '#F44336', major: '#FF9800', minor: '#2196F3', info: '#9E9E9E',
};

export default function InsightTimeline({ events }: InsightTimelineProps) {
  const router = useRouter();

  if (!events || events.length === 0) {
    return <Typography color="text.secondary">No insights timeline available</Typography>;
  }

  return (
    <Box sx={{ ml: 1 }}>
      {events.map((e, i) => (
        <Box key={e.id} sx={{ display: 'flex', gap: 2, pb: 2, borderLeft: i < events.length - 1 ? '2px solid' : 'none', borderColor: 'primary.main', pl: 2 }}>
          <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: severityColors[e.severity || 'info'] || '#9E9E9E', mt: 0.5, flexShrink: 0 }} />
          <Box sx={{ flex: 1, cursor: 'pointer' }} onClick={() => router.push(`/reports/${e.report_id}`)}>
            <Typography variant="caption" color="text.secondary">{e.report_date}</Typography>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mt: 0.25 }}>
              {e.severity && <Chip label={e.severity} size="small" sx={{ bgcolor: severityColors[e.severity] || '#9E9E9E', color: 'white', height: 18, fontSize: 10 }} />}
              <Typography variant="body2">{e.description || '(no description)'}</Typography>
            </Box>
            {e.impact && <Typography variant="caption" color="text.secondary">{e.impact}</Typography>}
          </Box>
        </Box>
      ))}
    </Box>
  );
}
