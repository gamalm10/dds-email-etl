'use client';

import { Card, CardContent, Typography, Chip, Skeleton, Box } from '@mui/material';

const CHIP_COLORS: Record<string, 'success' | 'warning' | 'error' | 'info' | 'default'> = {
  green: 'success',
  yellow: 'warning',
  red: 'error',
  blue: 'info',
  white: 'default',
  grey: 'default',
  unknown: 'default',
};

const DOT_COLORS: Record<string, string> = {
  green: '#4caf50',
  yellow: '#ff9800',
  red: '#f44336',
  blue: '#2196f3',
  white: '#9e9e9e',
  grey: '#9e9e9e',
  unknown: '#9e9e9e',
};

interface Props {
  history: any;
  loading: boolean;
}

export default function BrandTimeline({ history, loading }: Props) {
  if (loading) {
    return (
      <Card>
        <CardContent>
          <Skeleton variant="text" width={200} height={32} />
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} variant="rectangular" height={60} sx={{ mb: 1, borderRadius: 1 }} />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (!history?.reports?.length) return null;

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Report Timeline
        </Typography>
        <Box sx={{ position: 'relative', pl: 3 }}>
          {history.reports.map((r: any, i: number) => {
            const dotColor = DOT_COLORS[r.availability] || '#9e9e9e';
            const isLast = i === history.reports.length - 1;
            return (
              <Box
                key={i}
                sx={{
                  position: 'relative',
                  pb: isLast ? 0 : 2,
                  pl: 2,
                  borderLeft: isLast ? 'none' : `2px solid ${dotColor}`,
                  ml: '-2px',
                }}
              >
                <Box
                  sx={{
                    position: 'absolute',
                    left: -7,
                    top: 0,
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: dotColor,
                  }}
                />
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                  <Typography variant="subtitle2" fontWeight={600}>
                    {r.report_date}
                  </Typography>
                  <Chip
                    size="small"
                    color={CHIP_COLORS[r.availability] || 'default'}
                    label={r.availability}
                    sx={{ textTransform: 'capitalize' }}
                  />
                </Box>
                {r.milestone && (
                  <Typography variant="body2" color="text.secondary">
                    {r.milestone}
                  </Typography>
                )}
                {r.shipment_bis && (
                  <Typography variant="caption" color="text.secondary">
                    ETD: {r.shipment_bis}
                  </Typography>
                )}
                {r.comments && (
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                    {r.comments.slice(0, 120)}
                  </Typography>
                )}
              </Box>
            );
          })}
        </Box>
      </CardContent>
    </Card>
  );
}
