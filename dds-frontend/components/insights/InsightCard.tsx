'use client';
import { Card, CardContent, Typography, Chip, Box } from '@mui/material';
import { useRouter } from 'next/navigation';
import { navigate } from '@/components/common/navigate';

interface InsightCardProps {
  insight: {
    id: number;
    insight_type?: string | null;
    description: string;
    description_ar?: string | null;
    severity?: string | null;
    anomaly_score?: number | null;
    brand_id?: number | null;
    brand_name?: string | null;
    brand_category?: string | null;
    report_id?: number | null;
    report_date?: string | null;
    report_subject?: string | null;
    report_item_id?: number | null;
    vendor?: string | null;
    language?: string | null;
    impact?: string | null;
    recommendation?: string | null;
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
    else navigate(router, `/insights/${insight.id}`);
  };

  const category = insight.brand_category || insight.brand_name;
  const hasMeta = insight.report_id != null || insight.report_item_id != null || category || insight.vendor;

  return (
    <Card variant="outlined" sx={{ mb: 1, cursor: 'pointer' }} onClick={handleClick}>
      <CardContent sx={{ py: compact ? '8px !important' : '16px !important' }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, flexWrap: 'wrap' }}>
          {insight.severity && (
            <Chip label={insight.severity} size="small" sx={{ bgcolor: severityColors[insight.severity] || '#9E9E9E', color: 'white' }} />
          )}
          {insight.insight_type && (
            <Chip label={insight.insight_type.replace(/_/g, ' ')} size="small" variant="outlined" />
          )}
          {insight.anomaly_score != null && (
            <Chip label={`Anomaly: ${insight.anomaly_score}`} size="small" color="warning" variant="outlined" />
          )}
          <Box sx={{ flex: 1, minWidth: 200 }}>
            <Typography variant="body2" fontWeight={600}>{insight.description || '(no description)'}</Typography>
            {insight.description_ar && (
              <Typography variant="body2" dir="rtl" sx={{ fontFamily: 'Segoe UI, Tahoma, sans-serif', textAlign: 'right', mt: 0.5, color: 'text.secondary' }}>
                {insight.description_ar}
              </Typography>
            )}
          </Box>
        </Box>

        {hasMeta && (
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 1 }}>
            {insight.report_id != null && (
              <Chip size="small" variant="outlined"
                label={`Report #${insight.report_id}${insight.report_date ? ` · ${insight.report_date}` : ''}`}
                onClick={(e) => { e.stopPropagation(); navigate(router, `/reports/${insight.report_id}?hl=report-${insight.report_id}`); }} />
            )}
            {insight.report_item_id != null && insight.report_id != null && (
              <Chip size="small" color="primary" variant="outlined" label={`Item #${insight.report_item_id}`}
                onClick={(e) => { e.stopPropagation(); navigate(router, `/reports/${insight.report_id}?hl=item-${insight.report_item_id}`); }} />
            )}
            {category && (
              <Chip size="small" variant="outlined" label={category}
                onClick={(e) => { e.stopPropagation(); if (insight.brand_id != null) navigate(router, `/brands/${insight.brand_id}?hl=brand-${insight.brand_id}`); }} />
            )}
            {insight.vendor && <Chip size="small" variant="outlined" label={`Vendor: ${insight.vendor}`} />}
          </Box>
        )}

        {insight.report_subject && (
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
            {insight.report_subject}
          </Typography>
        )}

        {!compact && (insight.impact || insight.recommendation || insight.risk_tags) && (
          <Box sx={{ mt: 1 }}>
            {insight.impact && (
              <Typography variant="caption" color="text.secondary" display="block">Impact: {insight.impact}</Typography>
            )}
            {insight.recommendation && (
              <Typography variant="caption" color="success.main" display="block">Recommendation: {insight.recommendation}</Typography>
            )}
            {insight.risk_tags && (
              <Box sx={{ mt: 0.5 }}>
                {(() => {
                  try {
                    const tags = JSON.parse(insight.risk_tags);
                    return Array.isArray(tags) ? tags.map((tag: string) => (
                      <Chip key={tag} label={tag} size="small" variant="outlined" sx={{ mr: 0.5, mt: 0.5 }} />
                    )) : null;
                  } catch {
                    return <Typography variant="caption">{insight.risk_tags}</Typography>;
                  }
                })()}
              </Box>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
