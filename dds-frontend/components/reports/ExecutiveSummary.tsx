'use client';
import { useState } from 'react';
import { Box, Typography, Chip, Card, CardContent, LinearProgress } from '@mui/material';
import DrilldownModal from './DrilldownModal';

interface SummaryData {
  report_id: number;
  health_score: number;
  status_distribution: Record<string, number>;
  total_tasks: number;
  open_tasks: number;
  top_risks: Array<{ category: string; count: number }>;
  actions_by_person: Array<{ person: string; count: number }>;
  executive_text?: string;
}

interface Props {
  data: SummaryData;
  onDrilldown: (type: string, filter?: string) => void;
}

const statusColors: Record<string, string> = { green: '#4CAF50', yellow: '#FF9800', red: '#F44336', grey: '#9E9E9E', unknown: '#E0E0E0' };
const riskColors: Record<string, string> = { blocked: '#F44336', market_risk: '#FF9800', pricing_issue: '#2196F3', delay: '#9C27B0', supplier_failure: '#F44336', cancellation: '#F44336', escalation: '#FF5722' };

export default function ExecutiveSummary({ data, onDrilldown }: Props) {
  const [modalOpen, setModalOpen] = useState(false);
  const [modalTitle, setModalTitle] = useState('');
  const [modalData, setModalData] = useState<any[]>([]);
  const [modalEndpoint, setModalEndpoint] = useState('');

  const healthColor = data.health_score >= 80 ? '#4CAF50' : data.health_score >= 60 ? '#FF9800' : '#F44336';

  const openModal = async (title: string, endpoint: string) => {
    setModalTitle(title);
    setModalEndpoint(endpoint);
    setModalOpen(true);
    try {
      const res = await fetch(endpoint);
      const d = await res.json();
      setModalData(Array.isArray(d) ? d : []);
    } catch { setModalData([]); }
  };

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Executive Summary</Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" color="text.secondary">Health</Typography>
            <Typography variant="h5" fontWeight={700} color={healthColor}>{data.health_score}</Typography>
            <Typography variant="body2" color="text.secondary">/100</Typography>
          </Box>
        </Box>

        <LinearProgress variant="determinate" value={data.health_score}
          sx={{ mb: 2, height: 8, borderRadius: 4, bgcolor: '#E0E0E0', '& .MuiLinearProgress-bar': { bgcolor: healthColor } }} />

        {data.executive_text && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontStyle: 'italic', lineHeight: 1.6 }}>
            {data.executive_text}
          </Typography>
        )}

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          {Object.entries(data.status_distribution).map(([status, count]) => (
            <Chip key={status} label={`${status}: ${count}`}
              size="small" sx={{ bgcolor: statusColors[status] || '#E0E0E0', color: 'white', cursor: 'pointer' }}
              onClick={() => openModal(`${status} Items (${count})`, `/api/v1/reports/${data.report_id}/items?status=${status}`)} />
          ))}
        </Box>

        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Chip label={`${data.open_tasks} Open Tasks`} size="small" color="warning" variant="outlined"
            onClick={() => onDrilldown('tasks')} sx={{ cursor: 'pointer' }} />
          {data.actions_by_person.map((a) => (
            <Chip key={a.person} label={`${a.person}: ${a.count}`} size="small" variant="outlined"
              onClick={() => openModal(`${a.person}'s Actions`, `/api/v1/reports/${data.report_id}/actions?person=${a.person}`)}
              sx={{ cursor: 'pointer' }} />
          ))}
        </Box>

        {data.top_risks.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary">Top Risks</Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 0.5 }}>
              {data.top_risks.map((r) => (
                <Chip key={r.category} label={`${r.category}: ${r.count}`} size="small"
                  sx={{ bgcolor: riskColors[r.category] || '#9E9E9E', color: 'white', cursor: 'pointer' }}
                  onClick={() => openModal(`Risks: ${r.category}`, `/api/v1/reports/${data.report_id}/risks?category=${r.category}`)} />
              ))}
            </Box>
          </Box>
        )}
      </CardContent>

      <DrilldownModal open={modalOpen} title={modalTitle} data={modalData} endpoint={modalEndpoint}
        onClose={() => setModalOpen(false)} />
    </Card>
  );
}
