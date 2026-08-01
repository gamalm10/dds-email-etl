'use client';
import { Box, Typography, Chip } from '@mui/material';
import { useRouter } from 'next/navigation';

interface ActionEvent {
  id: number;
  person: string;
  action: string;
  urgency?: string | null;
  report_date?: string | null;
  report_id?: number;
  subject?: string;
}

interface ActionTimelineProps {
  events: ActionEvent[];
}

const urgencyColors: Record<string, string> = {
  high: '#F44336', medium: '#FF9800', low: '#4CAF50',
};

export default function ActionTimeline({ events }: ActionTimelineProps) {
  const router = useRouter();

  if (!events || events.length === 0) {
    return <Typography color="text.secondary">No actions timeline available</Typography>;
  }

  return (
    <Box sx={{ ml: 1 }}>
      {events.map((e, i) => (
        <Box key={e.id} sx={{ display: 'flex', gap: 2, pb: 2, borderLeft: i < events.length - 1 ? '2px solid' : 'none', borderColor: 'primary.main', pl: 2 }}>
          <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: urgencyColors[e.urgency || 'medium'] || '#9E9E9E', mt: 0.5, flexShrink: 0 }} />
          <Box sx={{ flex: 1, cursor: 'pointer' }} onClick={() => router.push(`/actions/${e.id}`)}>
            <Typography variant="caption" color="text.secondary">{e.report_date}</Typography>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mt: 0.25 }}>
              <Chip label={e.person} size="small" variant="outlined" sx={{ height: 18, fontSize: 10 }} />
              <Typography variant="body2">{e.action}</Typography>
            </Box>
            {e.subject && <Typography variant="caption" color="text.secondary">{e.subject}</Typography>}
          </Box>
        </Box>
      ))}
    </Box>
  );
}
