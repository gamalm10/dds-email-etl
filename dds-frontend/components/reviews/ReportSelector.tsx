'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import {
  TextField,
  Autocomplete,
  Button,
  CircularProgress,
  Box,
} from '@mui/material';
import CompareArrows from '@mui/icons-material/CompareArrows';

interface Report {
  id: number;
  subject: string;
  report_date: string;
}

interface Props {
  report1: number | null;
  report2: number | null;
  onChange1: (id: number | null) => void;
  onChange2: (id: number | null) => void;
  onCompare: () => void;
  loading: boolean;
}

export default function ReportSelector({ report1, report2, onChange1, onChange2, onCompare, loading }: Props) {
  const [reports, setReports] = useState<Report[]>([]);
  const [reportsLoading, setReportsLoading] = useState(true);

  useEffect(() => {
    api.get('v1/reports?limit=20')
      .then((res) => setReports(res.data))
      .catch(console.error)
      .finally(() => setReportsLoading(false));
  }, []);

  const selectedReport1 = reports.find((r) => r.id === report1) || null;
  const selectedReport2 = reports.find((r) => r.id === report2) || null;

  return (
    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
      <Autocomplete
        value={selectedReport1}
        onChange={(_, v) => onChange1(v?.id || null)}
        options={reports.filter((r) => r.id !== report2)}
        getOptionLabel={(r) => `#${r.id} - ${r.report_date} - ${r.subject.slice(0, 50)}`}
        loading={reportsLoading}
        sx={{ minWidth: 300, flex: 1 }}
        renderInput={(params) => (
          <TextField {...params} label="Report 1" />
        )}
      />
      <Autocomplete
        value={selectedReport2}
        onChange={(_, v) => onChange2(v?.id || null)}
        options={reports.filter((r) => r.id !== report1)}
        getOptionLabel={(r) => `#${r.id} - ${r.report_date} - ${r.subject.slice(0, 50)}`}
        loading={reportsLoading}
        sx={{ minWidth: 300, flex: 1 }}
        renderInput={(params) => (
          <TextField {...params} label="Report 2" />
        )}
      />
      <Button
        variant="contained"
        startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <CompareArrows />}
        onClick={onCompare}
        disabled={!report1 || !report2 || loading}
      >
        Compare
      </Button>
    </Box>
  );
}
