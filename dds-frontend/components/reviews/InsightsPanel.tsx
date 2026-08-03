'use client';

import { Card, CardContent, Typography, Chip, List, ListItem, Skeleton, Box } from '@mui/material';
import Info from '@mui/icons-material/Info';
import Warning from '@mui/icons-material/Warning';
import Error from '@mui/icons-material/Error';

const SEVERITY_ICONS: Record<string, any> = {
  high: <Error fontSize="small" color="error" />,
  medium: <Warning fontSize="small" color="warning" />,
  low: <Info fontSize="small" color="info" />,
  info: <Info fontSize="small" color="info" />,
};

interface Props {
  insights: any;
  brandHistory: any;
  loading: boolean;
}

export default function InsightsPanel({ insights, brandHistory, loading }: Props) {
  if (loading) {
    return (
      <Card>
        <CardContent>
          <Skeleton variant="text" width={140} height={32} />
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} variant="text" height={24} sx={{ mb: 0.5 }} />
          ))}
        </CardContent>
      </Card>
    );
  }

  const items = insights?.insights || [];
  const historyInsights = brandHistory?.insights || [];

  const allInsights = historyInsights.length > 0
    ? historyInsights
    : items.flatMap((g: any) => g.examples || []);

  if (allInsights.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Insights
          </Typography>
          <Typography variant="body2" color="text.secondary">
            No insights available for this brand.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Insights ({allInsights.length})
        </Typography>
        <List dense disablePadding>
          {allInsights.slice(0, 10).map((insight: any, i: number) => (
            <ListItem key={i} sx={{ px: 0, py: 0.75, flexDirection: 'column', alignItems: 'flex-start' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                {SEVERITY_ICONS[insight.severity] || SEVERITY_ICONS.info}
                <Typography variant="body2" sx={{ flex: 1 }}>
                  {insight.type && (
                    <Chip
                      size="small"
                      label={insight.type}
                      sx={{ mr: 0.5, fontSize: 10, height: 20 }}
                    />
                  )}
                  {insight.description}
                </Typography>
              </Box>
              {insight.recommendation && (
                <Typography variant="caption" color="text.secondary" sx={{ ml: 4, mt: 0.25 }}>
                  {insight.recommendation}
                </Typography>
              )}
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
