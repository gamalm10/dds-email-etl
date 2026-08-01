'use client';
import { Card, CardContent, Typography, Chip, Box } from '@mui/material';
import { useRouter } from 'next/navigation';

interface InsightCardProps {
  insight: {
    id: number;
    insight_type?: string | null;
    description: string;
    severity?: string | null;
    anomaly_score?: number | null;
    brand_id?: number | null;
    brand_name?: string | null;
    report_date?: string | null;
    impact?: string | null;
    risk_tags?: string | null;
  };
  onClick?: () => void;
  compact?: boolean;
}

const severityColors: Record<string, string> = {
  critical: '#F44336', major: '#FF9800', minor: '#2196F3', info: '#9E9E9E',
};

export default function InsightCard({ insight, onClick, compact }: InsightCardProps) {
  const router = useRouter();

  const handleClick = () => {
    if (onClick) onClick();
    else router.push(`/insights/${insight.id}`);
  };

  return (
    <Card variant="outlined" sx={{ mb: 1, cursor: 'pointer' }} onClick={handleClick}>
      <CardContent sx={{ py: compact ? '8px !important' : '16px !important' }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, flexWrap: 'wrap' }}>
          {insight.severity && (
            <Chip label={insight.severity} size="small" sx={{ bgcolor: severityColors[insight.severity] || '#9E9E9E', color: 'white' }} />
          )}
          <Box sx={{ flex: 1 }}>
            <Typography variant="body2" fontWeight={600}>{insight.description || '(no description)'}</Typography>
            {!compact && insight.impact && <Typography variant="caption" color="text.secondary">Impact: {insight.impact}</Typography>}
          </Box>
          {insight.brand_name && (
            <Chip label={insight.brand_name} size="small" variant="outlined" 
              onClick={(e) => { e.stopPropagation(); router.push(`/brands/${insight.brand_id}`); }} />
          )}
        </Box>
        {!compact && insight.risk_tags && (
          <Box sx={{ mt: 0.5 }}>
            {(() => {
              try { return JSON.parse(insight.risk_tags).map((tag: string) => (
                <Chip key={tag} label={tag} size="small" variant="outlined" sx={{ mr: 0.5, mt: 0.5 }} />
              )); } catch { return null; }
            })()}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
